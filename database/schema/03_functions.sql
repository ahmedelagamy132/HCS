-- ============================================================
-- HCS — Equine Intelligence System
-- 03_functions.sql  |  Utility functions & triggers
-- ============================================================

-- ── Auto-update updated_at timestamp ────────────────────────
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── Generate sequential entity codes (e.g. CLT-001) ─────────
-- Usage: SELECT fn_next_code('CLT', 'clients', 'client_code')
CREATE OR REPLACE FUNCTION fn_next_code(
    prefix    TEXT,
    tbl_name  TEXT,
    col_name  TEXT
)
RETURNS TEXT AS $$
DECLARE
    seq_n INTEGER;
    code  TEXT;
BEGIN
    EXECUTE format(
        'SELECT COALESCE(MAX(CAST(SUBSTRING(%I FROM %L) AS INTEGER)), 0) + 1 FROM %I WHERE %I ~ %L',
        col_name,
        '^' || prefix || '-([0-9]+)$',
        tbl_name,
        col_name,
        '^' || prefix || '-[0-9]+$'
    ) INTO seq_n;
    code := prefix || '-' || LPAD(seq_n::TEXT, 3, '0');
    RETURN code;
END;
$$ LANGUAGE plpgsql;

-- ── Recompute stable occupied count ─────────────────────────
CREATE OR REPLACE FUNCTION fn_refresh_stable_occupied()
RETURNS TRIGGER AS $$
BEGIN
    -- After any horse INSERT / UPDATE / DELETE, refresh stable's occupied count
    IF TG_OP = 'DELETE' THEN
        UPDATE stables
        SET occupied = (
            SELECT COUNT(*) FROM horses
            WHERE stable_id = OLD.stable_id AND is_active = TRUE
        )
        WHERE id = OLD.stable_id;
        RETURN OLD;
    ELSE
        -- Update old stable if horse moved
        IF OLD.stable_id IS DISTINCT FROM NEW.stable_id AND OLD.stable_id IS NOT NULL THEN
            UPDATE stables
            SET occupied = (
                SELECT COUNT(*) FROM horses
                WHERE stable_id = OLD.stable_id AND is_active = TRUE
            )
            WHERE id = OLD.stable_id;
        END IF;
        -- Update new stable
        IF NEW.stable_id IS NOT NULL THEN
            UPDATE stables
            SET occupied = (
                SELECT COUNT(*) FROM horses
                WHERE stable_id = NEW.stable_id AND is_active = TRUE
            )
            WHERE id = NEW.stable_id;
        END IF;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ── Auto-update horse health status from latest health record ─
CREATE OR REPLACE FUNCTION fn_sync_horse_health_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE horses
    SET health_status = NEW.status,
        updated_at    = NOW()
    WHERE id = NEW.horse_id
      AND NEW.status IS NOT NULL;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── Increment AI model request counter ──────────────────────
CREATE OR REPLACE FUNCTION fn_increment_model_requests()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        UPDATE ai_models
        SET total_requests = total_requests + 1,
            updated_at     = NOW()
        WHERE id = NEW.model_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── Log any table change to activity_logs ───────────────────
CREATE OR REPLACE FUNCTION fn_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    entity_id UUID;
BEGIN
    IF TG_OP = 'DELETE' THEN entity_id := OLD.id;
    ELSE entity_id := NEW.id;
    END IF;

    INSERT INTO activity_logs (
        actor_type, action, entity_type, entity_id, metadata
    ) VALUES (
        'system',
        LOWER(TG_OP),
        TG_TABLE_NAME,
        entity_id,
        jsonb_build_object(
            'table', TG_TABLE_NAME,
            'op', TG_OP,
            'ts', NOW()
        )
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- ── Hash password helper ────────────────────────────────────
CREATE OR REPLACE FUNCTION fn_hash_password(plain TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(plain, gen_salt('bf', 12));
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_check_password(plain TEXT, hashed TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN hashed = crypt(plain, hashed);
END;
$$ LANGUAGE plpgsql;
