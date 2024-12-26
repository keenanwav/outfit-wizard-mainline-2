--
-- PostgreSQL database dump
--

-- Dumped from database version 16.6
-- Dumped by pg_dump version 16.5

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
-- Name: cleanup_settings; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.cleanup_settings (
    id integer NOT NULL,
    max_age_hours integer DEFAULT 24 NOT NULL,
    cleanup_interval_hours integer DEFAULT 1 NOT NULL,
    batch_size integer DEFAULT 50 NOT NULL,
    max_workers integer DEFAULT 4 NOT NULL,
    last_cleanup timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.cleanup_settings OWNER TO neondb_owner;

--
-- Name: cleanup_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.cleanup_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cleanup_settings_id_seq OWNER TO neondb_owner;

--
-- Name: cleanup_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.cleanup_settings_id_seq OWNED BY public.cleanup_settings.id;


--
-- Name: clothing_items; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.clothing_items (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    style character varying(50) NOT NULL,
    color character varying(50) NOT NULL,
    image_path text,
    season character varying(20),
    tags text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer
);


ALTER TABLE public.clothing_items OWNER TO neondb_owner;

--
-- Name: clothing_items_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.clothing_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clothing_items_id_seq OWNER TO neondb_owner;

--
-- Name: clothing_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.clothing_items_id_seq OWNED BY public.clothing_items.id;


--
-- Name: item_color_history; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.item_color_history (
    id integer NOT NULL,
    item_id integer,
    color character varying(50),
    changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.item_color_history OWNER TO neondb_owner;

--
-- Name: item_color_history_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.item_color_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.item_color_history_id_seq OWNER TO neondb_owner;

--
-- Name: item_color_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.item_color_history_id_seq OWNED BY public.item_color_history.id;


--
-- Name: item_edit_history; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.item_edit_history (
    id integer NOT NULL,
    item_id integer,
    color character varying(50),
    style character varying(255),
    gender character varying(50),
    size character varying(50),
    hyperlink character varying(255),
    price numeric(10,2),
    edited_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.item_edit_history OWNER TO neondb_owner;

--
-- Name: item_edit_history_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.item_edit_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.item_edit_history_id_seq OWNER TO neondb_owner;

--
-- Name: item_edit_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.item_edit_history_id_seq OWNED BY public.item_edit_history.id;


--
-- Name: item_price_history; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.item_price_history (
    id integer NOT NULL,
    item_id integer,
    price numeric(10,2) NOT NULL,
    changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.item_price_history OWNER TO neondb_owner;

--
-- Name: item_price_history_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.item_price_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.item_price_history_id_seq OWNER TO neondb_owner;

--
-- Name: item_price_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.item_price_history_id_seq OWNED BY public.item_price_history.id;


--
-- Name: orphaned_items_audit; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.orphaned_items_audit (
    id integer NOT NULL,
    original_id integer,
    type character varying(50),
    image_path character varying(255),
    removed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.orphaned_items_audit OWNER TO neondb_owner;

--
-- Name: orphaned_items_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.orphaned_items_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.orphaned_items_audit_id_seq OWNER TO neondb_owner;

--
-- Name: orphaned_items_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.orphaned_items_audit_id_seq OWNED BY public.orphaned_items_audit.id;


--
-- Name: recycle_bin; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.recycle_bin (
    id integer NOT NULL,
    original_id integer,
    type character varying(50),
    color character varying(50),
    style character varying(255),
    gender character varying(50),
    size character varying(50),
    image_path character varying(255),
    hyperlink character varying(255),
    tags text[],
    season character varying(10),
    notes text,
    price numeric(10,2),
    deleted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.recycle_bin OWNER TO neondb_owner;

--
-- Name: recycle_bin_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.recycle_bin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recycle_bin_id_seq OWNER TO neondb_owner;

--
-- Name: recycle_bin_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.recycle_bin_id_seq OWNED BY public.recycle_bin.id;


--
-- Name: saved_outfits; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.saved_outfits (
    id integer NOT NULL,
    outfit_id character varying(50),
    username character varying(50),
    image_path character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tags text[],
    season text,
    notes text,
    user_id integer
);


ALTER TABLE public.saved_outfits OWNER TO neondb_owner;

--
-- Name: saved_outfits_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.saved_outfits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.saved_outfits_id_seq OWNER TO neondb_owner;

--
-- Name: saved_outfits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.saved_outfits_id_seq OWNED BY public.saved_outfits.id;


--
-- Name: shared_outfits; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.shared_outfits (
    id integer NOT NULL,
    outfit_id integer NOT NULL,
    shared_by_user_id integer NOT NULL,
    shared_with_user_id integer NOT NULL,
    shared_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.shared_outfits OWNER TO neondb_owner;

--
-- Name: shared_outfits_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.shared_outfits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shared_outfits_id_seq OWNER TO neondb_owner;

--
-- Name: shared_outfits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.shared_outfits_id_seq OWNED BY public.shared_outfits.id;


--
-- Name: user_clothing_items; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.user_clothing_items (
    id integer NOT NULL,
    user_id character varying(50),
    type character varying(50),
    color character varying(50),
    style character varying(255),
    gender character varying(50),
    size character varying(50),
    image_path character varying(255),
    hyperlink character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tags text[],
    season text,
    notes text,
    price numeric(10,2)
);


ALTER TABLE public.user_clothing_items OWNER TO neondb_owner;

--
-- Name: user_clothing_items_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.user_clothing_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_clothing_items_id_seq OWNER TO neondb_owner;

--
-- Name: user_clothing_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.user_clothing_items_id_seq OWNED BY public.user_clothing_items.id;


--
-- Name: user_items; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.user_items (
    id integer NOT NULL,
    type character varying(50),
    color character varying(50),
    style text[],
    gender text[],
    size text[],
    image_path text,
    hyperlink text,
    tags text[],
    season character varying(10),
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_items OWNER TO neondb_owner;

--
-- Name: user_items_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.user_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_items_id_seq OWNER TO neondb_owner;

--
-- Name: user_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.user_items_id_seq OWNED BY public.user_items.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash bytea NOT NULL,
    role character varying(10) DEFAULT 'user'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    full_name character varying(100),
    bio text,
    profile_picture_path character varying(255),
    preferences jsonb DEFAULT '{}'::jsonb,
    last_login timestamp without time zone,
    two_factor_secret character varying(32),
    two_factor_enabled boolean DEFAULT false,
    email_verified boolean DEFAULT false,
    verification_code character varying(6),
    verification_code_expires timestamp without time zone,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'user'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: cleanup_settings id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cleanup_settings ALTER COLUMN id SET DEFAULT nextval('public.cleanup_settings_id_seq'::regclass);


--
-- Name: clothing_items id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.clothing_items ALTER COLUMN id SET DEFAULT nextval('public.clothing_items_id_seq'::regclass);


--
-- Name: item_color_history id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.item_color_history ALTER COLUMN id SET DEFAULT nextval('public.item_color_history_id_seq'::regclass);


--
-- Name: item_edit_history id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.item_edit_history ALTER COLUMN id SET DEFAULT nextval('public.item_edit_history_id_seq'::regclass);


--
-- Name: item_price_history id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.item_price_history ALTER COLUMN id SET DEFAULT nextval('public.item_price_history_id_seq'::regclass);


--
-- Name: orphaned_items_audit id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.orphaned_items_audit ALTER COLUMN id SET DEFAULT nextval('public.orphaned_items_audit_id_seq'::regclass);


--
-- Name: recycle_bin id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.recycle_bin ALTER COLUMN id SET DEFAULT nextval('public.recycle_bin_id_seq'::regclass);


--
-- Name: saved_outfits id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.saved_outfits ALTER COLUMN id SET DEFAULT nextval('public.saved_outfits_id_seq'::regclass);


--
-- Name: shared_outfits id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.shared_outfits ALTER COLUMN id SET DEFAULT nextval('public.shared_outfits_id_seq'::regclass);


--
-- Name: user_clothing_items id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_clothing_items ALTER COLUMN id SET DEFAULT nextval('public.user_clothing_items_id_seq'::regclass);


--
-- Name: user_items id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_items ALTER COLUMN id SET DEFAULT nextval('public.user_items_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: cleanup_settings; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.cleanup_settings (id, max_age_hours, cleanup_interval_hours, batch_size, max_workers, last_cleanup, created_at, updated_at) FROM stdin;
1	24	1	50	4	2024-12-14 01:51:12.778826	2024-11-13 10:41:37.159041	2024-12-14 01:51:12.778826
\.


--
-- Data for Name: clothing_items; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.clothing_items (id, type, style, color, image_path, season, tags, created_at, user_id) FROM stdin;
\.


--
-- Data for Name: item_color_history; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.item_color_history (id, item_id, color, changed_at) FROM stdin;
\.


--
-- Data for Name: item_edit_history; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.item_edit_history (id, item_id, color, style, gender, size, hyperlink, price, edited_at) FROM stdin;
\.


--
-- Data for Name: item_price_history; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.item_price_history (id, item_id, price, changed_at) FROM stdin;
1	39	65.00	2024-11-13 23:48:22.281003
4	42	64.00	2024-11-15 01:19:30.198546
5	43	64.00	2024-11-15 01:20:29.616002
6	44	64.00	2024-11-15 01:24:13.387239
8	46	64.00	2024-11-15 01:27:50.615438
9	47	49.99	2024-11-15 01:29:21.752232
10	48	49.99	2024-11-15 01:29:55.096743
11	49	15.00	2024-11-15 01:30:51.367421
12	50	52.00	2024-11-15 01:32:14.838268
13	51	115.00	2024-11-15 01:33:41.180209
14	52	135.00	2024-11-15 01:35:36.211807
15	53	66.00	2024-11-15 01:36:45.174576
16	54	66.00	2024-11-15 01:37:35.397672
17	55	24.99	2024-11-15 01:39:12.073197
19	57	72.00	2024-11-15 01:40:36.13986
20	58	62.00	2024-11-15 01:41:45.607035
21	59	24.99	2024-11-15 01:43:17.377182
22	60	24.99	2024-11-15 01:44:23.117417
23	61	39.99	2024-11-15 01:45:30.929718
24	62	25.00	2024-11-15 01:46:38.810907
25	63	46.00	2024-11-15 01:47:49.916951
26	64	46.00	2024-11-15 01:48:36.013664
28	66	25.00	2024-11-15 01:51:01.985913
29	67	19.00	2024-11-15 01:52:29.383951
30	68	19.00	2024-11-15 01:53:25.107853
31	59	24.99	2024-11-20 01:32:00.756872
32	69	70.00	2024-11-25 03:24:32.642693
33	70	30.00	2024-11-25 03:38:14.119171
34	71	30.00	2024-11-25 03:53:47.266362
35	72	35.00	2024-11-25 04:11:07.497112
36	73	35.00	2024-11-25 04:15:12.446728
37	74	20.00	2024-11-26 01:48:49.514188
38	75	25.00	2024-11-26 01:56:16.173063
39	76	25.00	2024-11-26 01:58:40.525081
40	77	15.00	2024-11-26 02:03:18.61768
41	78	20.00	2024-11-26 02:09:03.336071
42	79	25.00	2024-11-26 02:16:23.336702
43	17	190.00	2024-11-26 02:19:20.374727
44	15	160.00	2024-11-26 02:20:44.684703
45	20	150.00	2024-11-26 02:21:54.898694
46	18	190.00	2024-11-26 02:22:42.38156
47	21	150.00	2024-11-26 02:23:19.467401
48	22	160.00	2024-11-26 02:24:31.079829
49	26	45.00	2024-11-26 02:25:57.809748
50	28	89.50	2024-11-26 02:26:47.454156
51	38	69.00	2024-11-26 02:28:14.320844
52	37	64.00	2024-11-26 02:28:57.069214
53	80	100.00	2024-11-26 10:57:52.607481
54	81	139.00	2024-11-26 11:30:49.664429
55	82	5.95	2024-11-26 11:35:05.566866
56	35	40.00	2024-11-26 11:36:27.686532
57	83	26.00	2024-11-26 11:41:20.29963
58	84	24.99	2024-11-26 11:52:36.624985
59	85	14.99	2024-11-26 11:58:24.754298
60	82	5.95	2024-11-26 12:03:37.463218
61	48	49.99	2024-11-26 13:33:56.493377
62	47	49.99	2024-11-26 13:35:21.93587
63	86	24.99	2024-11-26 23:50:24.243104
64	87	24.99	2024-11-27 00:01:40.4087
66	89	14.99	2024-11-27 00:48:11.374308
67	90	19.00	2024-11-27 03:32:37.567854
68	91	58.80	2024-11-27 03:34:05.061463
69	92	60.00	2024-11-27 11:41:27.422915
70	93	40.00	2024-11-27 11:45:35.069652
71	94	45.00	2024-11-27 11:51:01.81794
72	95	10.50	2024-11-27 12:06:54.339592
74	97	18.00	2024-11-30 03:28:24.833536
75	98	64.99	2024-12-02 02:47:14.403698
76	99	25.00	2024-12-09 07:55:55.586036
77	100	25.00	2024-12-09 07:56:45.507946
78	101	30.00	2024-12-09 07:57:55.352047
79	102	25.00	2024-12-09 07:58:58.549372
80	103	25.00	2024-12-09 07:59:38.950685
81	104	20.00	2024-12-09 08:00:39.631233
82	105	27.99	2024-12-09 08:01:41.769075
83	106	27.99	2024-12-09 08:02:30.697161
84	107	27.99	2024-12-09 08:03:09.718634
85	108	27.99	2024-12-09 08:04:19.224406
86	109	27.99	2024-12-09 08:05:01.124985
87	110	16.99	2024-12-09 08:05:45.120196
88	111	20.00	2024-12-09 08:06:36.392355
89	112	20.00	2024-12-09 08:07:24.234708
90	113	27.99	2024-12-09 08:08:53.00458
91	114	27.99	2024-12-09 08:09:31.032199
92	115	27.99	2024-12-09 08:10:16.532631
93	116	20.00	2024-12-09 08:12:01.919826
94	117	38.00	2024-12-09 08:13:00.251926
95	118	38.00	2024-12-09 08:13:39.44088
96	119	38.00	2024-12-09 08:14:14.912198
97	120	81.00	2024-12-09 08:19:09.449366
98	121	76.00	2024-12-09 08:20:11.902657
99	122	57.00	2024-12-09 08:21:26.655016
100	123	27.00	2024-12-09 08:22:10.078528
101	124	125.00	2024-12-09 08:23:44.868539
102	125	64.00	2024-12-09 08:24:34.147821
103	126	93.00	2024-12-09 08:25:17.820959
104	127	113.00	2024-12-09 08:26:28.960136
105	128	54.00	2024-12-09 08:27:32.67973
106	129	54.00	2024-12-09 08:28:20.004448
107	130	54.00	2024-12-09 08:29:24.011486
108	131	54.00	2024-12-09 08:29:59.07813
109	132	105.00	2024-12-09 08:34:42.69934
110	133	25.00	2024-12-11 05:01:35.846626
111	134	25.00	2024-12-11 05:02:07.487382
112	135	30.00	2024-12-11 05:02:55.658487
113	136	25.00	2024-12-11 05:03:42.853103
114	137	25.00	2024-12-11 05:04:11.519772
115	138	20.00	2024-12-11 05:05:26.084879
116	139	27.99	2024-12-11 05:07:34.136239
117	140	27.99	2024-12-11 05:08:01.112711
118	141	27.99	2024-12-11 05:08:32.844516
119	142	27.99	2024-12-11 05:10:21.576884
120	143	27.99	2024-12-11 05:10:52.610919
121	144	16.99	2024-12-11 05:11:46.354238
122	145	20.00	2024-12-11 05:12:28.916236
123	146	20.00	2024-12-11 05:23:16.201403
124	147	27.99	2024-12-11 05:24:19.991872
125	148	27.99	2024-12-11 05:25:05.370103
126	149	25.00	2024-12-14 18:32:58.31492
127	150	30.00	2024-12-14 18:34:37.844567
128	151	25.00	2024-12-17 02:23:54.823897
129	152	25.00	2024-12-17 02:26:35.229869
130	153	20.00	2024-12-17 02:27:39.308776
131	154	20.00	2024-12-17 02:28:54.225888
132	155	27.99	2024-12-17 02:29:39.105464
133	156	27.99	2024-12-17 02:30:17.297989
134	157	27.99	2024-12-17 02:31:02.541807
135	158	27.99	2024-12-17 02:31:37.226774
136	159	27.99	2024-12-17 02:32:15.682249
137	160	16.99	2024-12-17 02:33:32.769174
138	161	20.00	2024-12-17 02:34:22.264684
139	162	20.00	2024-12-17 02:35:18.610068
140	163	27.99	2024-12-17 02:36:33.122413
141	164	27.99	2024-12-17 02:37:06.64847
142	165	27.99	2024-12-17 02:37:45.136471
143	166	20.00	2024-12-17 02:38:29.642025
144	167	38.00	2024-12-18 01:07:08.662562
145	168	38.00	2024-12-18 01:07:50.855099
146	169	38.00	2024-12-18 01:08:34.524068
147	170	81.00	2024-12-18 01:09:19.276487
148	171	76.00	2024-12-18 01:10:04.205742
149	172	57.00	2024-12-18 01:10:53.259917
150	173	27.00	2024-12-18 01:11:42.444696
151	174	125.00	2024-12-18 01:13:35.413336
152	175	64.00	2024-12-18 01:14:25.70329
153	176	93.00	2024-12-18 01:15:14.597773
154	177	113.00	2024-12-18 01:16:16.81118
155	178	54.00	2024-12-18 01:16:55.353061
156	179	54.00	2024-12-18 01:17:39.531685
157	180	54.00	2024-12-18 01:18:13.905709
158	181	54.00	2024-12-18 01:18:44.975983
159	182	105.00	2024-12-18 01:19:28.874377
\.


--
-- Data for Name: orphaned_items_audit; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.orphaned_items_audit (id, original_id, type, image_path, removed_at) FROM stdin;
1	69	shirt	user_images/shirt_27aff558-a576-4db9-b0f1-abac62e9a156.png	2024-11-29 23:29:42.668113
2	70	shirt	user_images/shirt_d4f8937f-c2db-47e0-9b22-aa1999508784.png	2024-11-29 23:29:42.668113
3	71	shirt	user_images/shirt_9f5c5c17-6e10-4474-a607-2fd3ac42b34a.png	2024-11-29 23:29:42.668113
4	72	shirt	user_images/shirt_2ec05460-fea4-4fe9-a959-4ffab2da9178.png	2024-11-29 23:29:42.668113
5	73	shirt	user_images/shirt_54b562ba-32d3-47f9-af38-8df8edeabe10.png	2024-11-29 23:29:42.668113
6	74	shirt	user_images/shirt_a7e9c809-bc84-45d6-b0a6-e51902f28f24.png	2024-11-29 23:29:42.668113
7	75	shirt	user_images/shirt_37704ae5-90d5-4f47-ab72-fae3ca77f35f.png	2024-11-29 23:29:42.668113
8	76	shirt	user_images/shirt_2ae71c34-2fea-4518-94a2-16741c88fad5.png	2024-11-29 23:29:42.668113
9	77	shirt	user_images/shirt_70c655c3-016d-4015-a36c-80bd2d36d138.png	2024-11-29 23:29:42.668113
10	78	shirt	user_images/shirt_dfbf298f-b1de-4668-a02b-8c1bba517b23.png	2024-11-29 23:29:42.668113
11	79	pants	user_images/pants_6c570aed-97c0-4b4f-972b-4acbe9763b66.png	2024-11-29 23:29:42.668113
12	80	shoes	user_images/shoes_409ef336-003b-4262-b58c-60f2e96f2c5b.png	2024-11-29 23:29:42.668113
13	81	shirt	user_images/shirt_18d2bdfe-766f-4c95-b718-c74707acf014.png	2024-11-29 23:29:42.668113
14	83	shirt	user_images/shirt_503c384b-451f-464a-aa1a-877e5e49f05e.png	2024-11-29 23:29:42.668113
15	84	shirt	user_images/shirt_212eb1fe-c6a0-40dd-8b61-1a4473ff9f7c.png	2024-11-29 23:29:42.668113
16	85	shirt	user_images/shirt_3bafb241-3321-4fc0-a42d-a588e6deaaa0.png	2024-11-29 23:29:42.668113
17	82	shirt	user_images/shirt_48f8a65e-349d-4062-9e4d-9769fe6f52a3.png	2024-11-29 23:29:42.668113
18	86	shirt	user_images/shirt_aa9b702a-75b4-42b9-a121-f67c5634274a.png	2024-11-29 23:29:42.668113
19	87	pants	user_images/pants_7bd67724-3f8c-4087-b8ce-a6842089a12f.png	2024-11-29 23:29:42.668113
20	89	pants	user_images/pants_85def299-5535-4a0f-824f-197fda7c8801.png	2024-11-29 23:29:42.668113
21	90	pants	user_images/pants_83bfec66-f22e-406e-bb64-6dea92ecaa60.png	2024-11-29 23:29:42.668113
22	91	pants	user_images/pants_0a896ee5-2fc4-4df6-af43-d7528860b6ff.png	2024-11-29 23:29:42.668113
23	92	pants	user_images/pants_dbb3f537-48ad-423d-b7f6-ab3a4f74a150.png	2024-11-29 23:29:42.668113
24	93	pants	user_images/pants_55cb3539-3880-4a4a-9ab9-7a8b38faf3f1.png	2024-11-29 23:29:42.668113
25	94	shoes	user_images/shoes_05e4e761-0b46-4bbd-9943-5ad29d12544d.png	2024-11-29 23:29:42.668113
26	95	shoes	user_images/shoes_c155b74e-0638-4416-a753-c828032e9dd4.png	2024-11-29 23:29:42.668113
27	97	shoes	user_images/shoes_2edb9e02-468b-4957-becb-b2d933d48a4a.png	2024-11-30 16:52:51.579811
28	121	pants	user_images/pants_af5bb3a0-2707-44e1-9e48-52913a5556cc.png	2024-12-10 23:32:06.646527
29	122	pants	user_images/pants_fe99c3c8-b0fd-4658-afcb-7b916a01b8d8.png	2024-12-10 23:32:06.646527
30	99	shirt	user_images/shirt_b2d5e665-c9df-45b1-9061-d9d0c418991c.png	2024-12-10 23:32:06.646527
31	100	shirt	user_images/shirt_ec2a8aef-76db-4e56-99d8-ebf300f87369.png	2024-12-10 23:32:06.646527
32	101	shirt	user_images/shirt_3e693004-75a8-48df-b3c5-84880ed4df2a.png	2024-12-10 23:32:06.646527
33	102	shirt	user_images/shirt_9f254924-810b-479b-887f-7210ea146c91.png	2024-12-10 23:32:06.646527
34	103	shirt	user_images/shirt_e6303027-f44e-4f08-b098-e9c7e282a9d3.png	2024-12-10 23:32:06.646527
35	104	shirt	user_images/shirt_30371026-f05b-486d-ba51-66da357f24f4.png	2024-12-10 23:32:06.646527
36	105	shirt	user_images/shirt_0f1fd1fd-db81-4eb3-932b-0a20bd4f5163.png	2024-12-10 23:32:06.646527
37	106	shirt	user_images/shirt_8581d1a4-98aa-40d8-ae5a-6e2d98b3c8ce.png	2024-12-10 23:32:06.646527
38	107	shirt	user_images/shirt_f99f9af7-3f48-47ee-92d9-0ccb85059bce.png	2024-12-10 23:32:06.646527
39	108	shirt	user_images/shirt_821e6109-3291-4c0a-b999-cd2754fdc2f2.png	2024-12-10 23:32:06.646527
40	109	shirt	user_images/shirt_12fcc8bf-5cf5-4389-8cf8-0cd3cf2ab441.png	2024-12-10 23:32:06.646527
41	110	shirt	user_images/shirt_16989d72-4418-46a4-8e6e-63f1deb29cea.png	2024-12-10 23:32:06.646527
42	111	shirt	user_images/shirt_aeda2de2-9d32-454d-aac1-b7caa1c513f9.png	2024-12-10 23:32:06.646527
43	112	shirt	user_images/shirt_87bb1175-b6ca-4ea2-a063-97c50fa1cae0.png	2024-12-10 23:32:06.646527
44	113	shirt	user_images/shirt_d0431d05-b39c-431c-be2d-622f0a678efc.png	2024-12-10 23:32:06.646527
45	114	shirt	user_images/shirt_347f59ad-b14d-45da-9726-8064694f822c.png	2024-12-10 23:32:06.646527
46	115	shirt	user_images/shirt_cf183837-88e4-4710-a2d2-3a5307b08034.png	2024-12-10 23:32:06.646527
47	116	shirt	user_images/shirt_3b1c737f-489f-4ac5-b427-764aa87fea12.png	2024-12-10 23:32:06.646527
48	117	shirt	user_images/shirt_01142ba7-fea8-44da-929f-6c34e1a8622b.png	2024-12-10 23:32:06.646527
49	118	shirt	user_images/shirt_34635e3b-ef4e-4411-82b7-5df7ecc25b53.png	2024-12-10 23:32:06.646527
50	119	shirt	user_images/shirt_c529521e-de44-417a-aae0-db7dce8adca8.png	2024-12-10 23:32:06.646527
51	120	pants	user_images/pants_37eb153b-3b9d-4008-bca3-9e28fcd1d74b.png	2024-12-10 23:32:06.646527
52	123	pants	user_images/pants_d944d569-652e-4aeb-a497-fcb4b739ccfa.png	2024-12-10 23:32:06.646527
53	124	pants	user_images/pants_609a0fb0-5bb9-4230-8b29-bcca30e7256a.png	2024-12-10 23:32:06.646527
54	125	pants	user_images/pants_49cf8d7f-8cd5-4daf-93b9-3fb704eb1733.png	2024-12-10 23:32:06.646527
55	126	pants	user_images/pants_e5127574-8093-4dd7-a1cd-400a965cf6fd.png	2024-12-10 23:32:06.646527
56	127	shirt	user_images/shirt_d2e06280-ccb7-4308-a761-c26b7042d90b.png	2024-12-10 23:32:06.646527
57	128	shirt	user_images/shirt_e3027cd5-c924-4987-9e60-5cf50b1e6f3b.png	2024-12-10 23:32:06.646527
58	129	shirt	user_images/shirt_e85d3b1f-fd57-4c8b-9747-adc73232ea78.png	2024-12-10 23:32:06.646527
59	130	shirt	user_images/shirt_571a33d8-e18e-49b6-a61b-0e6bb104968a.png	2024-12-10 23:32:06.646527
60	131	shirt	user_images/shirt_c3833c8e-7282-4f41-8a8f-03b8a1d51c8d.png	2024-12-10 23:32:06.646527
61	132	pants	user_images/pants_ffc7f4b5-e632-44a6-a6dd-1a2be0ec5f16.png	2024-12-10 23:32:06.646527
\.


--
-- Data for Name: recycle_bin; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.recycle_bin (id, original_id, type, color, style