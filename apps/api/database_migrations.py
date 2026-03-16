from sqlalchemy.engine import Engine


def ensure_user_schema_columns(engine: Engine) -> None:
    with engine.begin() as conn:
        try:
            rows = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
            existing = {row[1] for row in rows}

            if "role" not in existing:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'")
            if "status" not in existing:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active'")

            conn.exec_driver_sql("UPDATE users SET role='user' WHERE role IS NULL OR role='' ")
            conn.exec_driver_sql("UPDATE users SET status='active' WHERE status IS NULL OR status='' ")
        except Exception:
            pass


def ensure_telegram_link_table(engine: Engine) -> None:
    with engine.begin() as conn:
        try:
            conn.exec_driver_sql(
                """
                CREATE TABLE IF NOT EXISTS telegram_links (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    telegram_user_id BIGINT NOT NULL UNIQUE,
                    telegram_chat_id BIGINT NOT NULL,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_telegram_links_telegram_user_id ON telegram_links(telegram_user_id)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_telegram_links_telegram_chat_id ON telegram_links(telegram_chat_id)")
        except Exception:
            pass


def ensure_subscription_table(engine: Engine) -> None:
    with engine.begin() as conn:
        try:
            conn.exec_driver_sql(
                """
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    plan VARCHAR(32) NOT NULL DEFAULT 'pro',
                    source VARCHAR(32) NOT NULL DEFAULT 'telegram_stars',
                    amount_usd FLOAT NOT NULL DEFAULT 1.99,
                    starts_at DATETIME NOT NULL,
                    expires_at DATETIME NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'active',
                    telegram_payment_charge_id VARCHAR(255),
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_user_subscriptions_user_id ON user_subscriptions(user_id)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_user_subscriptions_expires_at ON user_subscriptions(expires_at)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_user_subscriptions_status ON user_subscriptions(status)")
        except Exception:
            pass
