--
-- PostgreSQL database dump
--

\restrict ejmbdbGPmjEXSWc8h3GBtee7zoBEU0qUT0NRgD6q9bYCBAt1LllTvLzlRbXhShi

-- Dumped from database version 15.19 (Debian 15.19-0+deb12u1)
-- Dumped by pg_dump version 15.19 (Debian 15.19-0+deb12u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: approval_decisions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.approval_decisions (
    id character varying(36) NOT NULL,
    approval_id character varying(36) NOT NULL,
    reviewer_id character varying(36) NOT NULL,
    decision character varying(16) NOT NULL,
    payload_digest character varying(64) NOT NULL,
    comment character varying(1024) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.approval_decisions OWNER TO postgres;

--
-- Name: approvals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.approvals (
    id character varying(36) NOT NULL,
    recommendation_id character varying(36) NOT NULL,
    payload_digest character varying(64) NOT NULL,
    status character varying(32) NOT NULL,
    required_approvals integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked boolean NOT NULL,
    revoked_by character varying(36),
    revoked_at timestamp with time zone
);


ALTER TABLE public.approvals OWNER TO postgres;

--
-- Name: audit_checkpoints; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_checkpoints (
    id character varying(36) NOT NULL,
    chain_env character varying(16) NOT NULL,
    chain_org character varying(64) NOT NULL,
    seq bigint NOT NULL,
    hash character varying(64) NOT NULL,
    event_count integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    note character varying(255) NOT NULL
);


ALTER TABLE public.audit_checkpoints OWNER TO postgres;

--
-- Name: audit_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_events (
    id bigint NOT NULL,
    chain_env character varying(16) NOT NULL,
    chain_org character varying(64) NOT NULL,
    seq bigint NOT NULL,
    "timestamp" character varying(40) NOT NULL,
    actor_id character varying(36),
    actor_label character varying(255) NOT NULL,
    action character varying(96) NOT NULL,
    resource_type character varying(64) NOT NULL,
    resource_id character varying(255),
    payload jsonb NOT NULL,
    canonical text NOT NULL,
    prev_hash character varying(64) NOT NULL,
    hash character varying(64) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.audit_events OWNER TO postgres;

--
-- Name: audit_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_events_id_seq OWNER TO postgres;

--
-- Name: audit_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_events_id_seq OWNED BY public.audit_events.id;


--
-- Name: connectors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.connectors (
    id character varying(36) NOT NULL,
    name character varying(96) NOT NULL,
    category character varying(64) NOT NULL,
    status character varying(32) NOT NULL
);


ALTER TABLE public.connectors OWNER TO postgres;

--
-- Name: execution_queue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.execution_queue (
    id character varying(36) NOT NULL,
    recommendation_id character varying(36) NOT NULL,
    connector character varying(96),
    status character varying(24) NOT NULL,
    irreversible boolean NOT NULL,
    rollback_eligible boolean NOT NULL,
    idempotency_key character varying(64),
    result jsonb NOT NULL,
    enqueued_by character varying(36),
    enqueued_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.execution_queue OWNER TO postgres;

--
-- Name: model_cost_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.model_cost_rates (
    id character varying(36) NOT NULL,
    model_ref character varying(64) NOT NULL,
    provider character varying(48) NOT NULL,
    currency character varying(8) DEFAULT 'USD'::character varying NOT NULL,
    rate_input_per_1k double precision DEFAULT '0'::double precision NOT NULL,
    rate_output_per_1k double precision DEFAULT '0'::double precision NOT NULL,
    rate_cached_input_per_1k double precision DEFAULT '0'::double precision NOT NULL,
    source_url character varying(255) DEFAULT ''::character varying NOT NULL,
    effective_date character varying(10) DEFAULT ''::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.model_cost_rates OWNER TO postgres;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id character varying(36) NOT NULL,
    user_id character varying(36),
    kind character varying(48) NOT NULL,
    title character varying(255) NOT NULL,
    body text NOT NULL,
    read boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: pause_states; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pause_states (
    id character varying(36) NOT NULL,
    scope character varying(16) NOT NULL,
    target character varying(96) NOT NULL,
    active boolean NOT NULL,
    reason character varying(512) NOT NULL,
    engaged_by character varying(36),
    engaged_at timestamp with time zone,
    released_by character varying(36),
    released_at timestamp with time zone
);


ALTER TABLE public.pause_states OWNER TO postgres;

--
-- Name: permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.permissions (
    id character varying(36) NOT NULL,
    name character varying(96) NOT NULL,
    resource character varying(48) NOT NULL,
    action character varying(48) NOT NULL,
    description character varying(255) NOT NULL
);


ALTER TABLE public.permissions OWNER TO postgres;

--
-- Name: policies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.policies (
    id character varying(36) NOT NULL,
    name character varying(128) NOT NULL,
    description text NOT NULL,
    rules jsonb NOT NULL,
    enabled boolean NOT NULL,
    version integer NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.policies OWNER TO postgres;

--
-- Name: recommendations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recommendations (
    id character varying(36) NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    category character varying(64) NOT NULL,
    tier character varying(32) NOT NULL,
    risk_level character varying(16) NOT NULL,
    action_payload jsonb NOT NULL,
    payload_digest character varying(64) NOT NULL,
    status character varying(32) NOT NULL,
    required_approvals integer NOT NULL,
    submitted_by character varying(36) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    irreversible boolean NOT NULL
);


ALTER TABLE public.recommendations OWNER TO postgres;

--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role_permissions (
    role_id character varying(36) NOT NULL,
    permission_id character varying(36) NOT NULL
);


ALTER TABLE public.role_permissions OWNER TO postgres;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id character varying(36) NOT NULL,
    name character varying(64) NOT NULL,
    description character varying(255) NOT NULL,
    is_system boolean NOT NULL
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: saved_audit_filters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.saved_audit_filters (
    id character varying(36) NOT NULL,
    owner_id character varying(36) NOT NULL,
    name character varying(120) NOT NULL,
    query jsonb NOT NULL,
    shared boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_default boolean DEFAULT false NOT NULL
);


ALTER TABLE public.saved_audit_filters OWNER TO postgres;

--
-- Name: sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sessions (
    id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    jti character varying(36) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked boolean NOT NULL
);


ALTER TABLE public.sessions OWNER TO postgres;

--
-- Name: settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.settings (
    id character varying(36) NOT NULL,
    key character varying(96) NOT NULL,
    value jsonb NOT NULL,
    version integer NOT NULL,
    updated_by character varying(36),
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.settings OWNER TO postgres;

--
-- Name: usage_aggregates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usage_aggregates (
    id character varying(36) NOT NULL,
    day character varying(10) NOT NULL,
    workflow_type character varying(48) NOT NULL,
    tenant_ref character varying(64) NOT NULL,
    product_ref character varying(64) NOT NULL,
    cohort character varying(16) DEFAULT ''::character varying NOT NULL,
    n_events integer DEFAULT 0 NOT NULL,
    metrics jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.usage_aggregates OWNER TO postgres;

--
-- Name: usage_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usage_events (
    id character varying(36) NOT NULL,
    event_type character varying(48) NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    env character varying(16) NOT NULL,
    schema_version integer DEFAULT 1 NOT NULL,
    workflow_type character varying(48) NOT NULL,
    workflow_run_id character varying(36) NOT NULL,
    actor_type character varying(16) NOT NULL,
    actor_id character varying(96) NOT NULL,
    account_ref character varying(64),
    tenant_ref character varying(64) NOT NULL,
    product_ref character varying(64) NOT NULL,
    cohort character varying(16),
    attribution character varying(16),
    result character varying(16) DEFAULT 'n/a'::character varying NOT NULL,
    error_class character varying(24),
    model_ref character varying(64),
    tokens_in integer,
    tokens_out integer,
    tokens_cached integer,
    work_unit_type character varying(24),
    work_units integer,
    est_cost_usd double precision,
    latency_ms integer,
    cache_hit boolean,
    approval_gate character varying(48),
    decision character varying(16),
    decision_latency_ms integer,
    outcome_type character varying(32),
    outcome_value integer,
    handling_seconds integer
);


ALTER TABLE public.usage_events OWNER TO postgres;

--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_roles (
    user_id character varying(36) NOT NULL,
    role_id character varying(36) NOT NULL
);


ALTER TABLE public.user_roles OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id character varying(36) NOT NULL,
    subject character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_service_identity boolean NOT NULL,
    is_stub boolean NOT NULL,
    disabled boolean NOT NULL,
    token_version integer NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: audit_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_events ALTER COLUMN id SET DEFAULT nextval('public.audit_events_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: approval_decisions approval_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.approval_decisions
    ADD CONSTRAINT approval_decisions_pkey PRIMARY KEY (id);


--
-- Name: approvals approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.approvals
    ADD CONSTRAINT approvals_pkey PRIMARY KEY (id);


--
-- Name: audit_checkpoints audit_checkpoints_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_checkpoints
    ADD CONSTRAINT audit_checkpoints_pkey PRIMARY KEY (id);


--
-- Name: audit_events audit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_pkey PRIMARY KEY (id);


--
-- Name: connectors connectors_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.connectors
    ADD CONSTRAINT connectors_name_key UNIQUE (name);


--
-- Name: connectors connectors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.connectors
    ADD CONSTRAINT connectors_pkey PRIMARY KEY (id);


--
-- Name: execution_queue execution_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.execution_queue
    ADD CONSTRAINT execution_queue_pkey PRIMARY KEY (id);


--
-- Name: model_cost_rates model_cost_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model_cost_rates
    ADD CONSTRAINT model_cost_rates_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: pause_states pause_states_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pause_states
    ADD CONSTRAINT pause_states_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: policies policies_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.policies
    ADD CONSTRAINT policies_name_key UNIQUE (name);


--
-- Name: policies policies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.policies
    ADD CONSTRAINT policies_pkey PRIMARY KEY (id);


--
-- Name: recommendations recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: saved_audit_filters saved_audit_filters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.saved_audit_filters
    ADD CONSTRAINT saved_audit_filters_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: audit_events uq_chain_seq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT uq_chain_seq UNIQUE (chain_env, chain_org, seq);


--
-- Name: approval_decisions uq_one_decision_per_reviewer; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.approval_decisions
    ADD CONSTRAINT uq_one_decision_per_reviewer UNIQUE (approval_id, reviewer_id);


--
-- Name: usage_aggregates uq_usage_aggregate_group; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usage_aggregates
    ADD CONSTRAINT uq_usage_aggregate_group UNIQUE (day, workflow_type, tenant_ref, product_ref, cohort);


--
-- Name: usage_aggregates usage_aggregates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usage_aggregates
    ADD CONSTRAINT usage_aggregates_pkey PRIMARY KEY (id);


--
-- Name: usage_events usage_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usage_events
    ADD CONSTRAINT usage_events_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_approval_decisions_approval_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_approval_decisions_approval_id ON public.approval_decisions USING btree (approval_id);


--
-- Name: ix_approvals_payload_digest; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_approvals_payload_digest ON public.approvals USING btree (payload_digest);


--
-- Name: ix_approvals_recommendation_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_approvals_recommendation_id ON public.approvals USING btree (recommendation_id);


--
-- Name: ix_audit_chain; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_chain ON public.audit_events USING btree (chain_env, chain_org, seq);


--
-- Name: ix_audit_checkpoints_chain_env; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_checkpoints_chain_env ON public.audit_checkpoints USING btree (chain_env);


--
-- Name: ix_audit_checkpoints_chain_org; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_checkpoints_chain_org ON public.audit_checkpoints USING btree (chain_org);


--
-- Name: ix_audit_events_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_events_action ON public.audit_events USING btree (action);


--
-- Name: ix_audit_events_chain_env; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_events_chain_env ON public.audit_events USING btree (chain_env);


--
-- Name: ix_audit_events_chain_org; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_events_chain_org ON public.audit_events USING btree (chain_org);


--
-- Name: ix_audit_events_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_events_hash ON public.audit_events USING btree (hash);


--
-- Name: ix_audit_events_resource_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_events_resource_type ON public.audit_events USING btree (resource_type);


--
-- Name: ix_execution_queue_idempotency_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_execution_queue_idempotency_key ON public.execution_queue USING btree (idempotency_key);


--
-- Name: ix_execution_queue_recommendation_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_execution_queue_recommendation_id ON public.execution_queue USING btree (recommendation_id);


--
-- Name: ix_execution_queue_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_execution_queue_status ON public.execution_queue USING btree (status);


--
-- Name: ix_model_cost_rates_model_ref; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_model_cost_rates_model_ref ON public.model_cost_rates USING btree (model_ref);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_pause_states_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_pause_states_active ON public.pause_states USING btree (active);


--
-- Name: ix_permissions_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);


--
-- Name: ix_recommendations_payload_digest; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_recommendations_payload_digest ON public.recommendations USING btree (payload_digest);


--
-- Name: ix_recommendations_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_recommendations_status ON public.recommendations USING btree (status);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_saved_audit_filters_owner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_saved_audit_filters_owner_id ON public.saved_audit_filters USING btree (owner_id);


--
-- Name: ix_sessions_jti; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_sessions_jti ON public.sessions USING btree (jti);


--
-- Name: ix_sessions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sessions_user_id ON public.sessions USING btree (user_id);


--
-- Name: ix_settings_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_settings_key ON public.settings USING btree (key);


--
-- Name: ix_usage_aggregates_day; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_aggregates_day ON public.usage_aggregates USING btree (day);


--
-- Name: ix_usage_aggregates_tenant_ref; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_aggregates_tenant_ref ON public.usage_aggregates USING btree (tenant_ref);


--
-- Name: ix_usage_events_account_ref; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_events_account_ref ON public.usage_events USING btree (account_ref);


--
-- Name: ix_usage_events_event_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_events_event_type ON public.usage_events USING btree (event_type);


--
-- Name: ix_usage_events_occurred_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_events_occurred_at ON public.usage_events USING btree (occurred_at);


--
-- Name: ix_usage_events_product_ref; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_events_product_ref ON public.usage_events USING btree (product_ref);


--
-- Name: ix_usage_events_tenant_ref; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_events_tenant_ref ON public.usage_events USING btree (tenant_ref);


--
-- Name: ix_usage_events_workflow_run_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_events_workflow_run_id ON public.usage_events USING btree (workflow_run_id);


--
-- Name: ix_usage_events_workflow_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usage_events_workflow_type ON public.usage_events USING btree (workflow_type);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_subject ON public.users USING btree (subject);


--
-- Name: approval_decisions approval_decisions_approval_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.approval_decisions
    ADD CONSTRAINT approval_decisions_approval_id_fkey FOREIGN KEY (approval_id) REFERENCES public.approvals(id) ON DELETE CASCADE;


--
-- Name: approval_decisions approval_decisions_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.approval_decisions
    ADD CONSTRAINT approval_decisions_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.users(id);


--
-- Name: approvals approvals_recommendation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.approvals
    ADD CONSTRAINT approvals_recommendation_id_fkey FOREIGN KEY (recommendation_id) REFERENCES public.recommendations(id) ON DELETE CASCADE;


--
-- Name: execution_queue execution_queue_recommendation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.execution_queue
    ADD CONSTRAINT execution_queue_recommendation_id_fkey FOREIGN KEY (recommendation_id) REFERENCES public.recommendations(id) ON DELETE CASCADE;


--
-- Name: recommendations recommendations_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(id);


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: saved_audit_filters saved_audit_filters_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.saved_audit_filters
    ADD CONSTRAINT saved_audit_filters_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO caul_staging_user;


--
-- Name: TABLE alembic_version; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.alembic_version TO caul_staging_user;


--
-- Name: TABLE approval_decisions; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.approval_decisions TO caul_staging_user;


--
-- Name: TABLE approvals; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.approvals TO caul_staging_user;


--
-- Name: TABLE audit_checkpoints; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE public.audit_checkpoints TO caul_staging_user;


--
-- Name: TABLE audit_events; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE public.audit_events TO caul_staging_user;


--
-- Name: SEQUENCE audit_events_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.audit_events_id_seq TO caul_staging_user;


--
-- Name: TABLE connectors; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.connectors TO caul_staging_user;


--
-- Name: TABLE execution_queue; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.execution_queue TO caul_staging_user;


--
-- Name: TABLE model_cost_rates; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.model_cost_rates TO caul_staging_user;


--
-- Name: TABLE notifications; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.notifications TO caul_staging_user;


--
-- Name: TABLE pause_states; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pause_states TO caul_staging_user;


--
-- Name: TABLE permissions; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.permissions TO caul_staging_user;


--
-- Name: TABLE policies; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.policies TO caul_staging_user;


--
-- Name: TABLE recommendations; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.recommendations TO caul_staging_user;


--
-- Name: TABLE role_permissions; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.role_permissions TO caul_staging_user;


--
-- Name: TABLE roles; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.roles TO caul_staging_user;


--
-- Name: TABLE saved_audit_filters; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.saved_audit_filters TO caul_staging_user;


--
-- Name: TABLE sessions; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sessions TO caul_staging_user;


--
-- Name: TABLE settings; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.settings TO caul_staging_user;


--
-- Name: TABLE usage_aggregates; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.usage_aggregates TO caul_staging_user;


--
-- Name: TABLE usage_events; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.usage_events TO caul_staging_user;


--
-- Name: TABLE user_roles; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.user_roles TO caul_staging_user;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.users TO caul_staging_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES  TO caul_staging_user;


--
-- PostgreSQL database dump complete
--

\unrestrict ejmbdbGPmjEXSWc8h3GBtee7zoBEU0qUT0NRgD6q9bYCBAt1LllTvLzlRbXhShi

