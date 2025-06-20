from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, List
from datetime import datetime, timedelta, date

engine = create_engine("sqlite:///database.db")


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    points: int = 0
    level: int = 1
    badges: str = ""  # comma separated badges


class Mission(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    description: str
    points: int
    type: str = "generic"
    goal: int = 1
    progress: int = 0
    expires_at: Optional[datetime] = None
    warning_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Achievement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    description: str
    awarded_at: datetime = Field(default_factory=datetime.utcnow)


class Reward(SQLModel, table=True):
    """Items that users can redeem with their points."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str
    cost: int


class Purchase(SQLModel, table=True):
    """Log of rewards purchased by users."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    reward_id: int = Field(foreign_key="reward.id")
    purchased_at: datetime = Field(default_factory=datetime.utcnow)


class WeeklyActivity(SQLModel, table=True):
    """Tracks number of messages sent by a user each week."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    week_start: datetime
    message_count: int = 0


# create tables
SQLModel.metadata.create_all(engine)


def get_session():
    return Session(engine)


def calculate_reward(mission: Mission) -> int:
    """Compute dynamic reward based on mission goal and type."""
    base = mission.points * max(1, mission.goal)
    if mission.type == "hard":
        base *= 2
    return base


def get_or_create_user(user_id: int) -> User:
    with get_session() as session:
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        if not user:
            user = User(id=user_id)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user


def reset_missions(user_id: int):
    with get_session() as session:
        statement = select(Mission).where(Mission.user_id == user_id)
        missions = session.exec(statement).all()
        for m in missions:
            session.delete(m)
        session.commit()


def assign_mission(
    user_id: int,
    description: str,
    points: int,
    days_valid: int | None = None,
    mission_type: str = "generic",
    goal: int = 1,
) -> Mission:
    """Create a mission for a user."""
    expires_at = None
    if days_valid is not None:
        expires_at = datetime.utcnow() + timedelta(days=days_valid)
    mission = Mission(
        user_id=user_id,
        description=description,
        points=points,
        type=mission_type,
        goal=goal,
        expires_at=expires_at,
    )
    with get_session() as session:
        session.add(mission)
        session.commit()
        session.refresh(mission)
    return mission


def update_mission_progress(
    user_id: int, mission_id: int, amount: int = 1
) -> Optional[Mission]:
    """Increment mission progress and complete if goal reached."""
    with get_session() as session:
        mission = session.get(Mission, mission_id)
        if not mission or mission.user_id != user_id:
            return None
        mission.progress += amount
        if mission.progress >= mission.goal:
            reward = calculate_reward(mission)
            user = session.get(User, user_id)
            if user:
                user.points += reward
                user.level = user.points // 100 + 1
                session.delete(mission)
                session.add(user)
                session.commit()
                return mission
        session.add(mission)
        session.commit()
        session.refresh(mission)
        return mission


def get_active_missions(user_id: int) -> List[Mission]:
    """Return missions that are not expired."""
    now = datetime.utcnow()
    with get_session() as session:
        statement = select(Mission).where(Mission.user_id == user_id)
        missions = session.exec(statement).all()
        return [m for m in missions if m.expires_at is None or m.expires_at > now]


def complete_mission(user_id: int, mission_id: int) -> Optional[Mission]:
    """Mark mission as completed and award points."""
    with get_session() as session:
        mission = session.get(Mission, mission_id)
        user = session.get(User, user_id)
        if not mission or not user or mission.user_id != user_id:
            return None
        reward = calculate_reward(mission)
        user.points += reward
        user.level = user.points // 100 + 1
        session.delete(mission)
        session.add(user)
        session.commit()
        session.refresh(user)
        return mission


def remove_expired_missions() -> None:
    """Delete missions past their expiry date."""
    now = datetime.utcnow()
    with get_session() as session:
        statement = select(Mission).where(
            Mission.expires_at != None, Mission.expires_at < now
        )
        missions = session.exec(statement).all()
        for m in missions:
            session.delete(m)
        session.commit()


def get_missions_near_expiry(hours: int = 24) -> List[Mission]:
    """Return missions that will expire within the given hours and haven't been warned."""
    threshold = datetime.utcnow() + timedelta(hours=hours)
    with get_session() as session:
        statement = select(Mission).where(
            Mission.expires_at != None,
            Mission.expires_at <= threshold,
            Mission.expires_at > datetime.utcnow(),
            Mission.warning_sent == False,
        )
        missions = session.exec(statement).all()
        return missions


def mark_warning_sent(mission_id: int) -> None:
    with get_session() as session:
        mission = session.get(Mission, mission_id)
        if mission:
            mission.warning_sent = True
            session.add(mission)
            session.commit()


def get_all_users() -> List[User]:
    """Return all registered users."""
    with get_session() as session:
        statement = select(User)
        return session.exec(statement).all()


def get_top_users(limit: int = 10) -> List[User]:
    """Return users ordered by points descending."""
    with get_session() as session:
        statement = select(User).order_by(User.points.desc()).limit(limit)
        return session.exec(statement).all()


def assign_daily_missions(
    description: str,
    points: int,
    goal: int = 1,
) -> None:
    """Assign a daily mission to all users if they don't have it for today."""
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)
    with get_session() as session:
        users = session.exec(select(User)).all()
        for user in users:
            statement = select(Mission).where(
                Mission.user_id == user.id,
                Mission.type == "daily",
                Mission.created_at >= start,
                Mission.created_at < end,
            )
            exists = session.exec(statement).first()
            if not exists:
                mission = Mission(
                    user_id=user.id,
                    description=description,
                    points=points,
                    type="daily",
                    goal=goal,
                    expires_at=end,
                )
                session.add(mission)
        session.commit()


def assign_weekly_missions(
    description: str,
    points: int,
    goal: int = 1,
) -> None:
    """Assign a weekly mission to all users if they don't have it for this week."""
    today = datetime.utcnow().date()
    # Calculate Monday of the current week
    monday = today - timedelta(days=today.weekday())
    start = datetime.combine(monday, datetime.min.time())
    end = start + timedelta(days=7)
    with get_session() as session:
        users = session.exec(select(User)).all()
        for user in users:
            statement = select(Mission).where(
                Mission.user_id == user.id,
                Mission.type == "weekly",
                Mission.created_at >= start,
                Mission.created_at < end,
            )
            exists = session.exec(statement).first()
            if not exists:
                mission = Mission(
                    user_id=user.id,
                    description=description,
                    points=points,
                    type="weekly",
                    goal=goal,
                    expires_at=end,
                )
                session.add(mission)
        session.commit()


def get_weekly_mission(user_id: int) -> Optional[Mission]:
    """Return the active weekly mission for the given user."""
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    start = datetime.combine(monday, datetime.min.time())
    end = start + timedelta(days=7)
    with get_session() as session:
        statement = select(Mission).where(
            Mission.user_id == user_id,
            Mission.type == "weekly",
            Mission.created_at >= start,
            Mission.created_at < end,
        )
        return session.exec(statement).first()


def award_achievement(user_id: int, name: str, description: str) -> Achievement:
    """Grant an achievement and update user badges."""
    achievement = Achievement(
        user_id=user_id,
        name=name,
        description=description,
    )
    with get_session() as session:
        session.add(achievement)
        user = session.get(User, user_id)
        if user:
            badges = {b for b in user.badges.split(",") if b}
            badges.add(name)
            user.badges = ",".join(badges)
            session.add(user)
        session.commit()
        session.refresh(achievement)
        return achievement


def get_user_achievements(user_id: int) -> List[Achievement]:
    """Return all achievements for a user."""
    with get_session() as session:
        statement = select(Achievement).where(Achievement.user_id == user_id)
        return session.exec(statement).all()


def add_reward(name: str, description: str, cost: int) -> Reward:
    """Create a new reward available in the store."""
    reward = Reward(name=name, description=description, cost=cost)
    with get_session() as session:
        session.add(reward)
        session.commit()
        session.refresh(reward)
        return reward


def get_rewards() -> List[Reward]:
    """Return all available rewards."""
    with get_session() as session:
        statement = select(Reward)
        return session.exec(statement).all()


def redeem_reward(user_id: int, reward_id: int) -> Reward | None:
    """Deduct points from user and redeem the selected reward."""
    with get_session() as session:
        user = session.get(User, user_id)
        reward = session.get(Reward, reward_id)
        if not user or not reward or user.points < reward.cost:
            return None
        user.points -= reward.cost
        purchase = Purchase(user_id=user_id, reward_id=reward_id)
        session.add(user)
        session.add(purchase)
        session.commit()
        session.refresh(reward)
        return reward


def get_user_purchases(user_id: int) -> List[Purchase]:
    """Return purchases made by the given user."""
    with get_session() as session:
        statement = select(Purchase).where(Purchase.user_id == user_id)
        return session.exec(statement).all()


def _week_start(date: date) -> datetime:
    monday = date - timedelta(days=date.weekday())
    return datetime.combine(monday, datetime.min.time())


def record_user_message(user_id: int) -> None:
    """Increase weekly message count for a user."""
    start = _week_start(datetime.utcnow().date())
    with get_session() as session:
        statement = select(WeeklyActivity).where(
            WeeklyActivity.user_id == user_id,
            WeeklyActivity.week_start == start,
        )
        stat = session.exec(statement).first()
        if not stat:
            stat = WeeklyActivity(user_id=user_id, week_start=start)
        stat.message_count += 1
        session.add(stat)
        session.commit()


def get_weekly_activity(limit: int = 5, week: date | None = None) -> List[WeeklyActivity]:
    """Return top weekly activity for the given week."""
    week_start = _week_start(week or datetime.utcnow().date())
    with get_session() as session:
        statement = (
            select(WeeklyActivity)
            .where(WeeklyActivity.week_start == week_start)
            .order_by(WeeklyActivity.message_count.desc())
            .limit(limit)
        )
        return session.exec(statement).all()


def get_user_weekly_stat(user_id: int) -> Optional[WeeklyActivity]:
    start = _week_start(datetime.utcnow().date())
    with get_session() as session:
        statement = select(WeeklyActivity).where(
            WeeklyActivity.user_id == user_id,
            WeeklyActivity.week_start == start,
        )
        return session.exec(statement).first()


def reward_top_weekly_users(
    week: date, top_n: int = 3, points: int = 10
) -> list[User]:
    """Award extra points to the most active users of the given week."""
    week_start = _week_start(week)
    with get_session() as session:
        statement = (
            select(WeeklyActivity)
            .where(WeeklyActivity.week_start == week_start)
            .order_by(WeeklyActivity.message_count.desc())
            .limit(top_n)
        )
        stats = session.exec(statement).all()
        rewarded: list[User] = []
        for stat in stats:
            user = session.get(User, stat.user_id)
            if user:
                user.points += points
                user.level = user.points // 100 + 1
                session.add(user)
        rewarded.append(user)
    session.commit()
    return rewarded


def get_monthly_purchase_summary(month: date) -> list[tuple[Reward | None, int]]:
    """Return count of purchases per reward for the given month."""
    start = datetime(month.year, month.month, 1)
    if month.month == 12:
        next_month = datetime(month.year + 1, 1, 1)
    else:
        next_month = datetime(month.year, month.month + 1, 1)

    with get_session() as session:
        statement = select(Purchase).where(
            Purchase.purchased_at >= start,
            Purchase.purchased_at < next_month,
        )
        purchases = session.exec(statement).all()
        counts: dict[int, int] = {}
        for p in purchases:
            counts[p.reward_id] = counts.get(p.reward_id, 0) + 1

        rewards = {}
        if counts:
            statement = select(Reward).where(Reward.id.in_(list(counts.keys())))
            rewards = {r.id: r for r in session.exec(statement).all()}

        return [(rewards.get(rid), count) for rid, count in counts.items()]
