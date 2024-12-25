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
    notes text
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

COPY public.recycle_bin (id, original_id, type, color, style, gender, size, image_path, hyperlink, tags, season, notes, price, deleted_at) FROM stdin;
\.


--
-- Data for Name: saved_outfits; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.saved_outfits (id, outfit_id, username, image_path, created_at, tags, season, notes) FROM stdin;
2	caa863f0-4130-43da-b142-7e6c38d2151e	default_user	wardrobe/outfit_caa863f0-4130-43da-b142-7e6c38d2151e.png	2024-11-01 03:07:31.208476	\N	\N	\N
48	9c4ee6ef-b847-49f6-a2e6-bad4db17a3db	\N	wardrobe/outfit_9c4ee6ef-b847-49f6-a2e6-bad4db17a3db.png	2024-12-09 19:51:51.735068	{"Casual "}	Fall	Nice colors 😌😌😌😌
15	c462434b-6fca-48ae-aa57-cedcafb9fe51	\N	wardrobe/outfit_c462434b-6fca-48ae-aa57-cedcafb9fe51.png	2024-11-09 17:29:52.517542	\N	\N	\N
16	a425fe87-4267-4267-be58-8700213abdbb	\N	wardrobe/outfit_a425fe87-4267-4267-be58-8700213abdbb.png	2024-11-09 17:30:14.046658	\N	\N	\N
17	945674b2-aa9f-480c-9bdf-ee0a2a70327e	\N	wardrobe/outfit_945674b2-aa9f-480c-9bdf-ee0a2a70327e.png	2024-11-10 08:33:47.461506	\N	\N	\N
18	cdae4bec-300c-4124-8930-e13b4a6a414e	\N	wardrobe/outfit_cdae4bec-300c-4124-8930-e13b4a6a414e.png	2024-11-10 14:10:17.285158	\N	\N	\N
19	e212695d-72f4-4ea5-b193-0e612430ebde	\N	wardrobe/outfit_e212695d-72f4-4ea5-b193-0e612430ebde.png	2024-11-10 17:22:35.996994	\N	\N	\N
20	5ad7373c-cf75-4356-b444-3930352faf9f	\N	wardrobe/outfit_5ad7373c-cf75-4356-b444-3930352faf9f.png	2024-11-10 21:01:47.662061	\N	\N	\N
49	3f36e925-4811-4288-9259-4396f1135a04	\N	wardrobe/outfit_3f36e925-4811-4288-9259-4396f1135a04.png	2024-12-11 21:14:26.236605	\N	\N	\N
21	9133527e-c6e1-445b-ac56-6189662ef466	\N	wardrobe/outfit_9133527e-c6e1-445b-ac56-6189662ef466.png	2024-11-10 21:49:41.999886	\N	\N	None
22	6228db34-68b1-44ab-b9ae-0e1f688cfaf1	\N	wardrobe/outfit_6228db34-68b1-44ab-b9ae-0e1f688cfaf1.png	2024-11-14 16:53:47.262734	\N	\N	\N
23	265dffbe-1b6d-4484-9c74-0bd35476fc37	\N	wardrobe/outfit_265dffbe-1b6d-4484-9c74-0bd35476fc37.png	2024-11-14 20:01:27.558533	\N	\N	\N
25	9b072a08-3e47-4cd8-a99a-86737a85bf7b	\N	wardrobe/outfit_9b072a08-3e47-4cd8-a99a-86737a85bf7b.png	2024-11-16 01:25:19.322262	\N	\N	\N
26	5134ac92-ca11-4d37-9020-3ac2ddc41fb0	\N	wardrobe/outfit_5134ac92-ca11-4d37-9020-3ac2ddc41fb0.png	2024-11-17 18:53:33.111465	\N	\N	\N
27	3c48797b-53cb-4be9-9257-175054723797	\N	wardrobe/outfit_3c48797b-53cb-4be9-9257-175054723797.png	2024-11-19 01:14:44.749351	\N	\N	\N
28	9b6c07c3-dde7-45ad-830d-6b1e20e3197d	\N	wardrobe/outfit_9b6c07c3-dde7-45ad-830d-6b1e20e3197d.png	2024-11-20 01:43:06.235052	\N	\N	\N
29	1a70a726-6dd4-4216-b42b-7a0aa1d0d5c2	\N	wardrobe/outfit_1a70a726-6dd4-4216-b42b-7a0aa1d0d5c2.png	2024-11-20 02:05:33.204453	\N	\N	\N
30	9c466e7c-5af6-42c1-90c6-4694768e6a98	\N	wardrobe/outfit_9c466e7c-5af6-42c1-90c6-4694768e6a98.png	2024-11-20 02:41:44.230543	\N	\N	\N
24	b181c92d-85ac-4668-a907-feb15c9806c4	\N	wardrobe/outfit_b181c92d-85ac-4668-a907-feb15c9806c4.png	2024-11-15 01:57:29.086473	\N	\N	None
31	794c20dc-3e8b-4161-8f69-e6229d23cac8	\N	wardrobe/outfit_794c20dc-3e8b-4161-8f69-e6229d23cac8.png	2024-11-20 16:54:41.790014	\N	\N	\N
32	79392f6b-fc89-4052-be82-26ce79277f6c	\N	wardrobe/outfit_79392f6b-fc89-4052-be82-26ce79277f6c.png	2024-11-20 16:57:08.544386	\N	\N	\N
33	6b13c2a8-d73f-4050-b4f2-ba95a84f958e	\N	wardrobe/outfit_6b13c2a8-d73f-4050-b4f2-ba95a84f958e.png	2024-11-21 09:39:57.391831	\N	\N	\N
34	0c3c985d-8695-4b89-91b0-f79f1426d675	\N	wardrobe/outfit_0c3c985d-8695-4b89-91b0-f79f1426d675.png	2024-11-24 18:35:37.980986	\N	\N	\N
35	10c37677-bb3b-453b-9bd7-dd8c21a73e09	\N	wardrobe/outfit_10c37677-bb3b-453b-9bd7-dd8c21a73e09.png	2024-11-24 23:31:15.008953	\N	\N	\N
36	215e045b-6d35-45dc-9e1d-a4557d04fa63	\N	wardrobe/outfit_215e045b-6d35-45dc-9e1d-a4557d04fa63.png	2024-11-25 14:41:35.603896	\N	\N	\N
39	f2641aa5-aba1-46b2-8a14-fe05c7407d1f	\N	wardrobe/outfit_f2641aa5-aba1-46b2-8a14-fe05c7407d1f.png	2024-11-25 15:33:34.029213	\N	\N	\N
41	4cf9825d-717d-47a0-8d12-f6a7c72430bd	\N	wardrobe/outfit_4cf9825d-717d-47a0-8d12-f6a7c72430bd.png	2024-11-26 13:44:08.728001	\N	\N	\N
42	bcdca021-9bb4-4be2-aa37-8a9f7f82a983	\N	wardrobe/outfit_bcdca021-9bb4-4be2-aa37-8a9f7f82a983.png	2024-11-27 12:07:35.512192	\N	\N	\N
43	5d2c4338-0e5f-4b48-ba71-0e72e676e53d	\N	wardrobe/outfit_5d2c4338-0e5f-4b48-ba71-0e72e676e53d.png	2024-11-28 20:40:17.420069	\N	\N	\N
50	b0538fba-3a7d-4643-b253-128f205cecc8	\N	wardrobe/outfit_b0538fba-3a7d-4643-b253-128f205cecc8.png	2024-12-11 21:15:11.802267	\N	\N	\N
45	b83d8629-1f7a-4f3f-9c32-af9049184426	\N	wardrobe/outfit_b83d8629-1f7a-4f3f-9c32-af9049184426.png	2024-12-02 02:51:16.441475	\N	\N	\N
46	bfab9722-0c0a-475e-aba7-f831658bb2b6	\N	wardrobe/outfit_bfab9722-0c0a-475e-aba7-f831658bb2b6.png	2024-12-09 08:43:48.273704	\N	\N	\N
47	fba1ba86-645e-4cd9-8cf3-b435c9ac97f4	\N	wardrobe/outfit_fba1ba86-645e-4cd9-8cf3-b435c9ac97f4.png	2024-12-09 08:44:28.964088	\N	\N	\N
51	5e7a0743-41a4-454f-bd26-e54f7f5837c0	\N	wardrobe/outfit_5e7a0743-41a4-454f-bd26-e54f7f5837c0.png	2024-12-11 21:15:24.861778	\N	\N	\N
52	399e59d7-92b7-49f4-978d-519394fed03b	\N	wardrobe/outfit_399e59d7-92b7-49f4-978d-519394fed03b.png	2024-12-11 21:16:22.858748	\N	\N	\N
54	ffecfa05-06e0-4394-9554-b2f5cf291f00	\N	wardrobe/outfit_ffecfa05-06e0-4394-9554-b2f5cf291f00.png	2024-12-16 13:43:03.777669	{"new outfits"}	Summer	take 1\n
53	4944a2ac-432a-4a66-9893-1f0a3e1e4223	\N	wardrobe/outfit_4944a2ac-432a-4a66-9893-1f0a3e1e4223.png	2024-12-16 13:41:57.376396	{#earthtones}	Spring	greens and brown go good together.
55	f0fe5608-6ab7-4f14-95e6-6c3117917f64	\N	wardrobe/outfit_f0fe5608-6ab7-4f14-95e6-6c3117917f64.png	2024-12-19 15:57:46.97338	\N	\N	\N
56	830cae20-f37e-42d3-93f7-e93086cb3220	\N	wardrobe/outfit_830cae20-f37e-42d3-93f7-e93086cb3220.png	2024-12-20 01:31:35.354365	\N	\N	\N
\.


--
-- Data for Name: user_clothing_items; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.user_clothing_items (id, user_id, type, color, style, gender, size, image_path, hyperlink, created_at, tags, season, notes, price) FROM stdin;
37	\N	pants	138,145,158	Casual	Male	S,M,L,XL	user_images/pants_19866edd-c42e-4aba-8338-ac8adef4cf39.png	https://www.jackjones.com/en-us/product/12268003_3561/slim-fit-jeans	2024-11-10 14:00:19.552124	\N	\N	\N	64.00
38	\N	pants	67,101,141	Casual	Male	S,M,L,XL	user_images/pants_0c330e18-cd84-4d30-bda8-840fca9dcc3d.png	https://www.jackjones.com/en-us/product/12261946_3561/wide-leg-fit-jeans	2024-11-10 14:01:05.861081	\N	\N	\N	69.00
5	\N	shirt	82,58,9	Casual	Male	XS,S,M,L,XL	user_images/shirt_b75e00d9-4f29-40ff-b040-cb0b57b35d66.png	https://www.youngandreckless.com/collections/mens-all/products/banner-tee-brown	2024-11-05 05:48:19.43671	\N	\N	\N	10.00
17	\N	shoes	211,186,138	Formal,Casual	Male	S,M,L,XL	user_images/shoes_0c3efc99-0869-48a7-8a81-2c5b6be2113e.png	https://www.clarks.com/en-us/nomad-loafer/26178112-p	2024-11-10 08:13:44.270359	\N	\N	\N	190.00
33	\N	shirt	234,235,239	Casual,Sport	Male	S,M,L,XL	user_images/shirt_82decbc7-8a4b-4d7d-9d4d-6e931a6523d3.png	https://www.jackjones.com/en-us/product/12263604_5_1135635/wide-fit-crew-neck-t-shirt	2024-11-10 13:57:22.446673	\N	\N	\N	10.00
30	\N	shirt	28,28,31	Casual,Sport	Male	S,M,L,XL	user_images/shirt_9426e4e5-7c4f-4ccc-8eb0-b10ae18c3bcd.png	https://www.jackjones.com/en-us/product/12255085_2161_1182000/regular-fit-round-neck-t-shirt	2024-11-10 13:54:43.18382	\N	\N	\N	10.00
86	\N	shirt	206,211,217	Casual	Female	S,M,L,XL	\N	https://www2.hm.com/en_us/productpage.1267555003.html	2024-11-26 23:50:24.243104	\N	\N	\N	24.99
34	\N	shirt	29,29,32	Casual,Sport	Male	S,M,L,XL	user_images/shirt_8a82e599-8e0a-440c-90a9-1a0e5415cfb2.png	https://www.jackjones.com/en-us/product/12263604_2161/wide-fit-crew-neck-t-shirt	2024-11-10 13:57:57.800382	\N	\N	\N	10.00
23	\N	shirt	181,181,181	Casual,Sport	Unisex,Male	S,M,L,XL	user_images/shirt_b02f6043-0727-40b8-9bc0-f9a1464ed201.png	https://www.thepopculture.co/products/the-college-dropout-bear-unisex-tee-old-kanye-west-inspired-tshirt	2024-11-10 13:43:22.847645	\N	\N	\N	10.00
31	\N	shirt	92,82,75	Casual,Sport	Male	S,M,L,XL	user_images/shirt_95959371-e94c-4785-89a5-88ef18778a09.png	https://www.jackjones.com/en-us/product/12280884_274/relaxed-fit-crew-neck-t-shirt	2024-11-10 13:55:22.344472	\N	\N	\N	10.00
87	\N	pants	23,22,23	Casual,Formal	Female	S,M,L,XL	\N	https://www2.hm.com/en_us/productpage.1260945001.html	2024-11-27 00:01:40.4087	\N	\N	\N	24.99
29	\N	shirt	121,113,88	Casual,Sport	Male	S,M,L,XL	user_images/shirt_d4e0c46f-181a-41f5-8a5e-5ecf3347be9d.png	https://www.jackjones.com/en-us/product/12255085_4263_1182000/regular-fit-round-neck-t-shirt	2024-11-10 13:53:52.019631	\N	\N	\N	10.00
27	\N	shirt	254,170,65	Casual,Sport	Male,Unisex	S,M,L,XL	user_images/shirt_1de23997-0440-464f-b12c-23d06cd89d08.png	https://www.hollisterco.com/shop/wd/p/relaxed-mclaren-graphic-hoodie-56197335?categoryId=166245&faceout=prod&seq=02	2024-11-10 13:51:00.563603	\N	\N	\N	10.00
12	\N	shirt	0,131,255	Casual	Male	XS,S,M,L,XL	user_images/shirt_ab5b7a3b-ac67-4069-8e25-c2fcac340364.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/cracked-tee-royal-blue	2024-11-05 06:00:20.918218	\N	\N	\N	10.00
13	\N	shirt	195,191,191	Casual	Male	XS,S,M,L,XL	user_images/shirt_4d133099-4396-40d1-930a-2f0bcf8a04c7.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/descent-tee-grey	2024-11-05 06:01:50.291653	\N	\N	\N	10.00
15	\N	shoes	108,60,38	Formal	Male	S,M,L,XL	user_images/shoes_f5721652-f305-4efd-a17b-c22821d739ff.png	https://www.clarks.com/en-us/desert-trek-hiker/26178208-p	2024-11-10 08:12:03.055163	\N	\N	\N	160.00
35	\N	shirt	23,36,49	Casual,Sport,Formal	Male	S,M,L,XL	user_images/shirt_e0f7ef39-9c7d-4b01-a093-cdd635092d89.png	https://www.jackjones.com/en-us/product/12136668_2078_624130/slim-fit-polo-polo-shirt	2024-11-10 13:58:41.478912	\N	\N	\N	40.00
28	\N	pants	104,94,61	Casual,Sport	Male	S,M,L,XL	user_images/pants_5f6a323c-a5b9-445c-b912-2b4db3a7cadc.png	https://www.jackjones.com/en-us/product/12242264_1926/relaxed-fit-normal-rise-rib-hems-cargo-pants	2024-11-10 13:52:17.846364	\N	\N	\N	89.50
11	\N	shirt	121,95,61	Casual	Male	XS,S,M,L,XL	user_images/shirt_2e72596a-448c-410f-8753-a72ee1ff0da6.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/internal-tee-dark-chocolate	2024-11-05 05:58:38.177397	\N	\N	\N	10.00
89	\N	pants	73,73,74	Casual	Female	S,M,L,XL	\N	https://www2.hm.com/en_us/productpage.0768912001.html	2024-11-27 00:48:11.374308	\N	\N	\N	14.99
8	\N	pants	99,113,74	Casual	Male	XS,S,M,L,XL	user_images/pants_4eaf78d2-434e-44bb-8fd1-53dd94d8678c.png	https://mnml.la/products/mnml-pants-bootcut-cargo-pants-m2020-p886-cam	2024-11-05 05:54:01.913763	\N	\N	\N	10.00
18	\N	shoes	225,181,142	Formal	Male,Unisex	S,M,L,XL	user_images/shoes_d591b7b1-6b5a-4c9d-b41e-93c349d91b57.png	https://www.clarks.com/en-us/rossendale-desert/26178031-p	2024-11-10 08:15:31.457915	\N	\N	\N	190.00
26	\N	pants	173,104,49	Casual,Formal,Sport	Male	S,M,L,XL	user_images/pants_8789580e-19fa-49fe-bc28-76511cd4eccb.png	https://www.jackjones.com/en-us/product/12150148_562/slim-fit-low-rise-chinos	2024-11-10 13:45:52.307386	\N	\N	\N	45.00
22	\N	shoes	19,26,55	Formal,Casual	Male,Unisex	S,M,L,XL	user_images/shoes_14c41396-9a62-475f-b785-e5f659ea0346.png	https://www.clarks.com/en-us/wallabee/26178225-p	2024-11-10 08:23:02.394786	\N	\N	\N	160.00
19	\N	shoes	14,13,11	Formal	Male	S,M,L,XL	user_images/shoes_70c3ce22-7a48-4d8e-a8d8-808b530d4ad7.png	https://www.clarks.com/en-us/wallabee/26155519-p	2024-11-10 08:16:49.896945	\N	\N	\N	10.00
32	\N	shirt	154,179,199	Casual,Sport	Male	S,M,L,XL	user_images/shirt_af0723c3-a644-4da5-ad0a-96313b791aea.png	https://www.jackjones.com/en-us/product/12262491_8403/relaxed-fit-crew-neck-t-shirt	2024-11-10 13:56:42.140869	\N	\N	\N	10.00
21	\N	shoes	145,126,93	Formal,Casual	Male	S,M,L,XL	user_images/shoes_569b78ba-738f-447b-b485-0db3a813d3b9.png	https://www.clarks.com/en-us/wallabee/26155515-p	2024-11-10 08:19:43.148881	\N	\N	\N	150.00
20	\N	shoes	96,52,27	Formal	Male	S,M,L,XL	user_images/shoes_13467291-2d0a-44d0-a07b-b83a04d72020.png	https://www.clarks.com/en-us/wallabee/26155518-p	2024-11-10 08:18:08.058333	\N	\N	\N	150.00
6	\N	shirt	190,177,158	Casual,Sporty	Male	XS,S,M,L,XL	user_images/shirt_b59f13c8-dc2e-4925-9056-b20bbd498f4a.png	https://www.youngandreckless.com/collections/mens-all/products/big-r-script-tee-sand	2024-11-05 05:49:57.169325	\N	\N	\N	10.00
90	\N	pants	68,64,69	Casual	Female	S,M,L,XL	\N	https://www2.hm.com/en_us/productpage.1250617004.html	2024-11-27 03:32:37.567854	\N	\N	\N	19.00
91	\N	pants	118,157,184	Casual	Female	S,M,L,XL	\N	https://www.levi.com/US/en_US/clothing/women/jeans/straight/wedgie-straight-fit-womens-jeans/p/349640198	2024-11-27 03:34:05.061463	\N	\N	\N	58.80
39	\N	shoes	230,229,234	Casual,Sport	Male,Unisex	S,M,L,XL	user_images/shoes_74929657-e3ae-48b0-8d65-33cc32210d1a.png	https://www.converse.com/shop/p/chuck-taylor-all-star-canvas-unisex-high-top-shoe/M9006MP.html?pid=M9006MP&dwvar_M9006MP_color=optical%20white&dwvar_M9006MP_width=standard&styleNo=M7650&pdp=true	2024-11-13 23:48:22.281003	\N	\N	\N	65.00
9	\N	shoes	72,22,26	Casual,Formal,Sporty	Male,Unisex	XS,S,M,L,XL	user_images/shoes_441f282d-21dc-4fc1-8f49-cb5a5b3ca853.png	https://www.converse.com/shop/p/chuck-taylor-all-star-canvas-unisex-high-top-shoe/M9006MP.html?pid=M9006MP&dwvar_M9006MP_color=maroon&dwvar_M9006MP_width=standard&styleNo=M9613&pdp=true	2024-11-05 05:56:08.151323	\N	\N	\N	10.00
42	\N	pants	161,112,89	Casual,Sport	Male	S,M,L,XL	user_images/pants_fd0c41b0-3aef-4a62-95d4-0a373c11c6c6.png	https://killionest.com/collections/bottoms/products/cargo-twill-trekker-pant-rust	2024-11-15 01:19:30.198546	\N	\N	\N	64.00
43	\N	pants	95,78,67	Casual	Male	S,M,L,XL	user_images/pants_b6208889-aa9c-4e86-8668-fa67a82ed54a.png	https://killionest.com/collections/bottoms/products/cargo-twill-trekker-pant-black	2024-11-15 01:20:29.616002	\N	\N	\N	64.00
44	\N	pants	71,72,73	Casual	Male	S,M,L,XL	user_images/pants_f88d7d22-47de-41d7-be66-4b386534bc2b.png	https://killionest.com/collections/bottoms/products/cargo-twill-trekker-pant-black	2024-11-15 01:24:13.387239	\N	\N	\N	64.00
46	\N	shirt	84,117,162	Casual	Male	S,M,L,XL	user_images/shirt_0dbd1814-1f0b-4dac-9a75-f008a9e5f62c.png	 https://killionest.com/collections/denim/products/classic-13oz-denim-jacket-medium-blue	2024-11-15 01:27:50.615438	\N	\N	\N	64.00
49	\N	shirt	176,174,175	Casual,Sport	Male	S,M,L,XL	user_images/shirt_ce08caae-a050-4db5-853d-4766688af727.png	https://ethikworldwide.com/products/logistics-tee-1	2024-11-15 01:30:51.367421	\N	\N	\N	15.00
51	\N	shoes	224,224,222	Casual,Sport	Male	S,M,L,XL	user_images/shoes_30deaaa6-d2f2-45b2-a5dc-9278b0d8f0ce.png	https://www.footlocker.com/product/nike-air-force-1-low-mens/J9179200.html	2024-11-15 01:33:41.180209	\N	\N	\N	115.00
52	\N	shoes	169,123,79	Casual,Sport	Male	S,M,L,XL	user_images/shoes_43339fba-a2bd-49d0-bb7f-fb45d773b4c3.png	https://www.footlocker.com/product/~/J9179200.html	2024-11-15 01:35:36.211807	\N	\N	\N	135.00
53	\N	pants	113,87,70	Casual,Sport	Male	S,M,L,XL	user_images/pants_2c53e6bf-c884-45b4-a30f-70f91cd3a16d.png	https://ethikworldwide.com/products/nylon-bungee-pants-3	2024-11-15 01:36:45.174576	\N	\N	\N	66.00
54	\N	pants	134,124,86	Casual,Sport	Male	S,M,L,XL	user_images/pants_39b1da29-5ad3-44e6-b1ff-99a05ff55bfd.png	https://ethikworldwide.com/products/nylon-bungee-pants-1	2024-11-15 01:37:35.397672	\N	\N	\N	66.00
55	\N	pants	37,29,28	Casual,Formal	Male	S,M,L,XL	user_images/pants_2e6a3166-4ef2-4acc-b179-3e447b45a582.png	https://www2.hm.com/en_us/productpage.1240972004.html	2024-11-15 01:39:12.073197	\N	\N	\N	24.99
57	\N	shirt	68,62,62	Casual	Male	S,M,L,XL	user_images/shirt_f2b767b5-fa89-4d41-8458-7c602aa52280.png	https://ethikworldwide.com/products/sideline-jacket	2024-11-15 01:40:36.13986	\N	\N	\N	72.00
58	\N	pants	68,70,71	Casual	Male	S,M,L,XL	user_images/pants_d935fcb8-dada-43d2-8852-f52967296685.png	https://killionest.com/collections/denim/products/ab-001-black-distressed-denim-jeans	2024-11-15 01:41:45.607035	\N	\N	\N	62.00
60	\N	pants	71,70,74	Casual,Formal	Male	S,M,L,XL	user_images/pants_07b8ea5d-f7ab-4b03-ab64-d58be10e88cb.png	https://www2.hm.com/en_us/productpage.1074402002.html	2024-11-15 01:44:23.117417	\N	\N	\N	24.99
61	\N	pants	75,75,75	Casual,Formal	Male	S,M,L,XL	user_images/pants_16627fdc-37f5-4dc0-8a68-4effe3e7543c.png	https://www2.hm.com/en_us/productpage.1219626003.html	2024-11-15 01:45:30.929718	\N	\N	\N	39.99
62	\N	shirt	39,39,39	Casual	Male	S,M,L,XL	user_images/shirt_27d3781e-6843-4130-bc98-0848395834c8.png	https://ethikworldwide.com/products/strong-mint-tee-1	2024-11-15 01:46:38.810907	\N	\N	\N	25.00
63	\N	shirt	36,59,41	Casual	Male	S,M,L,XL	user_images/shirt_78c5e4dc-abb0-44d2-b61f-bf75c2c163b9.png	https://www.ronindivision.com/collections/frontpage/products/warriors-tee-forest	2024-11-15 01:47:49.916951	\N	\N	\N	46.00
67	\N	shirt	233,232,231	Casual,Sport,Beach	Male	S,M,L,XL	user_images/shirt_26120094-346e-484c-be6b-40fa017cb3c6.png	https://ethikworldwide.com/products/youre-always-on-your-phone-tee-1	2024-11-15 01:52:29.383951	\N	\N	\N	19.00
68	\N	pants	147,126,126	Casual,Sport,Beach	Male	S,M,L,XL	user_images/pants_d2002997-3b4d-4df9-9a9b-9880b41f7731.png	https://www.ronindivision.com/collections/frontpage/products/wavy-water-shorts-taupe	2024-11-15 01:53:25.107853	\N	\N	\N	19.00
47	\N	shoes	191,172,161	Sport	Male,Unisex,Female	S,M,L,XL	user_images/shoes_a1602b1b-9573-41ae-be4a-dc712eab45d9.png	https://www.crocs.com/p/classic-clog/10001.html?cgid=men-footwear&cid=6WC	2024-11-15 01:29:21.752232	\N	\N	\N	49.99
59	\N	pants	168,166,166	Casual,Formal	Male	S,M,L,XL	user_images/pants_422a5b02-b75b-41fd-80da-800c22bb200c.png	https://www2.hm.com/en_us/productpage.1234995004.html	2024-11-15 01:43:17.377182	\N	\N	\N	24.99
64	\N	shirt	210,210,210	Casual,Sport	Male	S,M,L,XL	user_images/shirt_a49030c9-ffcf-451e-8340-785802c7b62d.png	https://www.ronindivision.com/collections/frontpage/products/warriors-tee-heather-grey	2024-11-15 01:48:36.013664	\N	\N	\N	46.00
50	\N	shirt	148,150,152	Casual	Male	S,M,L,XL	user_images/shirt_031c7f19-5024-431a-856f-e0124aae4934.png	https://ethikworldwide.com/products/new-jack-crewneck-1	2024-11-15 01:32:14.838268	\N	\N	\N	52.00
48	\N	shoes	134,138,130	Sport	Male,Unisex	S,M,L,XL	user_images/shoes_b51e7556-e2de-45cb-8a09-d097830bfd53.png	https://www.crocs.com/p/classic-clog/10001.html?cgid=men-footwear&cid=6WC	2024-11-15 01:29:55.096743	\N	\N	\N	49.99
69	\N	shirt	147,145,130	Formal	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12263645_1714_1137226/comfort-fit-shirt-collar-shirt	2024-11-25 03:24:32.642693	\N	\N	\N	70.00
70	\N	shirt	108,110,117	Casual,Sport	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12285055_2042/relaxed-fit-crew-neck-t-shirt	2024-11-25 03:38:14.119171	\N	\N	\N	30.00
66	\N	shirt	100,89,76	Casual,Sport,Beach	Male	S,M,L,XL	user_images/shirt_acca8ef7-eaa9-49ce-8145-bc92e2dfa291.png	https://ethikworldwide.com/products/wings-tee	2024-11-15 01:51:01.985913	\N	\N	\N	25.00
71	\N	shirt	41,40,46	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12285060_2161/relaxed-fit-crew-neck-t-shirt	2024-11-25 03:53:47.266362	\N	\N	\N	30.00
72	\N	shirt	239,240,235	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12278457_6/loose-fit-crew-neck-t-shirt	2024-11-25 04:11:07.497112	\N	\N	\N	35.00
73	\N	shirt	240,238,244	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12285057_5/relaxed-fit-crew-neck-t-shirt	2024-11-25 04:15:12.446728	\N	\N	\N	35.00
74	\N	shirt	233,231,218	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12262491_4162/relaxed-fit-crew-neck-t-shirt	2024-11-26 01:48:49.514188	\N	\N	\N	20.00
75	\N	shirt	231,195,144	Casual,Beach	Male,Unisex	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12265826_19/wide-fit-crew-neck-t-shirt	2024-11-26 01:56:16.173063	\N	\N	\N	25.00
76	\N	shirt	44,51,93	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12265826_13046/wide-fit-crew-neck-t-shirt	2024-11-26 01:58:40.525081	\N	\N	\N	25.00
77	\N	shirt	85,66,55	Casual	Male,Unisex	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12255167_273_1107495/standard-fit-round-neck-t-shirt	2024-11-26 02:03:18.61768	\N	\N	\N	15.00
78	\N	shirt	102,98,92	Casual	Male,Unisex	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12256926_5/wide-fit-crew-neck-t-shirt	2024-11-26 02:09:03.336071	\N	\N	\N	20.00
79	\N	pants	145,143,148	Casual	Male	S,M,L,XL	\N	https://killionest.com/collections/bottoms/products/cargo-twill-trekker-pant-slate	2024-11-26 02:16:23.336702	\N	\N	\N	25.00
80	\N	shoes	180,181,172	Casual	Male	S,M,L,XL	\N	https://www.urbanoutfitters.com/shop/new-balance-530-sneaker2?category=mens-clothing&color=011&type=REGULAR&quantity=1	2024-11-26 10:57:52.607481	\N	\N	\N	100.00
81	\N	shirt	38,25,26	Casual,Formal,Beach	Female	S,M,L,XL	\N	https://www2.hm.com/en_us/productpage.1199483009.html	2024-11-26 11:30:49.664429	\N	\N	\N	139.00
83	\N	shirt	242,170,32	Casual	Male	S,M,L,XL	\N	https://anwarcarrots.com/collections/shop/products/hand-picked-tee-squash?variant=44882049630375	2024-11-26 11:41:20.29963	\N	\N	\N	26.00
84	\N	shirt	216,169,24	Casual	Female	S,M,L,XL	\N	https://www2.hm.com/en_us/productpage.1238852010.html	2024-11-26 11:52:36.624985	\N	\N	\N	24.99
85	\N	shirt	233,234,229	Casual	Female	S,M,L,XL	\N	https://www2.hm.com/en_us/productpage.1232418002.html	2024-11-26 11:58:24.754298	\N	\N	\N	14.99
82	\N	shirt	28,17,49	Casual	Female	S,M,L,XL	\N	https://www.shein.com/	2024-11-26 11:35:05.566866	\N	\N	\N	5.95
92	\N	pants	59,59,63	Casual	Female	S,M,L,XL	\N	https://www.prettylittlething.us/petite-black-micro-mini-pu-pleated-skirt.html	2024-11-27 11:41:27.422915	\N	\N	\N	60.00
93	\N	pants	176,131,118	Casual	Female	S,M,L,XL	\N	https://www.prettylittlething.us/multi-scenic-collage-printed-mesh-frilly-low-waist-mini-skirt.html	2024-11-27 11:45:35.069652	\N	\N	\N	40.00
94	\N	shoes	201,177,164	Casual	Female	S,M,L,XL	\N	https://www.prettylittlething.us/beige-faux-suede-buckled-mule-cloggs.html	2024-11-27 11:51:01.81794	\N	\N	\N	45.00
95	\N	shoes	233,184,169	Casual	Female	S,M,L,XL	\N	https://www.prettylittlething.us/tan-pu-padded-cross-over-strap-flat-sandals.html	2024-11-27 12:06:54.339592	\N	\N	\N	10.50
97	\N	shoes	201,177,164	Casual	Female	S,M,L,XL	\N	https://www.prettylittlething.us/beige-faux-suede-buckled-mule-cloggs.html	2024-11-30 03:27:44.826576	\N	\N	\N	18.00
98	\N	shoes	209,205,202	Casual,Sport	Male	S,M,L,XL	user_images/shoes_2e3d9983-4371-4f30-97f7-929dcf1016ab.png	https://www.amazon.com/dp/B09YBGQBF4?ref=cm_sw_r_cp_ud_dp_NRNMK73M4TN4JS7ZF1F3_1&ref_=cm_sw_r_cp_ud_dp_NRNMK73M4TN4JS7ZF1F3_1&social_share=cm_sw_r_cp_ud_dp_NRNMK73M4TN4JS7ZF1F3_1&starsLeft=1&skipTwisterOG=1&th=1&psc=1	2024-12-02 02:47:14.403698	\N	\N	\N	64.99
121	\N	pants	165,167,160	Casual	Male	S,M,L,XL	\N	https://mnml.la/products/mnml-denim-x511-denim-m2023-d884-blu	2024-12-09 08:20:11.902657	\N	\N	\N	76.00
122	\N	pants	186,185,183	Casual	Male	S,M,L,XL	\N	https://mnml.la/products/mnml-bottoms-relaxed-every-day-sweatpants-m2022-w634-gry	2024-12-09 08:21:26.655016	\N	\N	\N	57.00
99	\N	shirt	188,151,114	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12263521_1957/oversized-fit-crew-neck-t-shirt	2024-12-09 07:55:55.586036	\N	\N	\N	25.00
100	\N	shirt	197,204,196	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12263521_3/oversized-fit-crew-neck-t-shirt	2024-12-09 07:56:45.507946	\N	\N	\N	25.00
101	\N	shirt	236,228,214	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/pro duct/12282604_4162/relaxed-fit-crew-neck-t-shirt	2024-12-09 07:57:55.352047	\N	\N	\N	30.00
102	\N	shirt	229,230,235	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12262506_5/wide-fit-crew-neck-t-shirt	2024-12-09 07:58:58.549372	\N	\N	\N	25.00
103	\N	shirt	39,38,43	Casual	Male	S,M,L,XL	\N	https://www.jackjones.com/en-us/product/12262506_2161/wide-fit-crew-neck-t-shirt	2024-12-09 07:59:38.950685	\N	\N	\N	25.00
104	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/roses-tee-blac	2024-12-09 08:00:39.631233	\N	\N	\N	20.00
105	\N	shirt	189,169,54	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/test-your-luck-tee-natural	2024-12-09 08:01:41.769075	\N	\N	\N	27.99
106	\N	shirt	63,53,41	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/limited-edition-tee-dark-chocolate	2024-12-09 08:02:30.697161	\N	\N	\N	27.99
107	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/marathon-tee-black	2024-12-09 08:03:09.718634	\N	\N	\N	27.99
108	\N	shirt	226,224,231	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/problem-child-tee-white	2024-12-09 08:04:19.224406	\N	\N	\N	27.99
109	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/eye-of-the-storm-tee-natural	2024-12-09 08:05:01.124985	\N	\N	\N	27.99
110	\N	shirt	151,146,140	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/call-my-manager-tee-brown	2024-12-09 08:05:45.120196	\N	\N	\N	16.99
111	\N	shirt	33,68,127	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/better-as-one-tee-heather-grey	2024-12-09 08:06:36.392355	\N	\N	\N	20.00
112	\N	shirt	203,222,217	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/lifes-a-trip-tee-forest-green	2024-12-09 08:07:24.234708	\N	\N	\N	20.00
113	\N	shirt	111,152,217	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/explore-tee-white	2024-12-09 08:08:53.00458	\N	\N	\N	27.99
114	\N	shirt	189,214,221	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/world-tour-tee-light-blue	2024-12-09 08:09:31.032199	\N	\N	\N	27.99
115	\N	shirt	225,225,223	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/cracked-tee-white	2024-12-09 08:10:16.532631	\N	\N	\N	27.99
116	\N	shirt	224,225,228	Casual	Male	S,M,L,XL	\N	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/flower-district-tee-white	2024-12-09 08:12:01.919826	\N	\N	\N	20.00
117	\N	shirt	172,129,101	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/dog-will-hunt-t-shirt-2	2024-12-09 08:13:00.251926	\N	\N	\N	38.00
118	\N	shirt	193,64,51	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/bullrider-t-shirt-2	2024-12-09 08:13:39.44088	\N	\N	\N	38.00
119	\N	shirt	248,134,81	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/bullrider-t-shirt-2	2024-12-09 08:14:14.912198	\N	\N	\N	38.00
120	\N	pants	170,163,149	Casual	Male	S,M,L,XL	\N	https://mnml.la/products/mnml-denim-d152-cargo-denim-m2022-d617-bro	2024-12-09 08:19:09.449366	\N	\N	\N	81.00
123	\N	pants	112,100,147	Casual	Male	S,M,L,XL	\N	https://mnml.la/products/mnml-bottoms-tie-dye-cargo-pants-m2023-p566-pup?refSrc=6623059902536&nosto=productpage-nosto-1-copy-1722864312997	2024-12-09 08:22:10.078528	\N	\N	\N	27.00
124	\N	pants	120,112,124	Casual	Male	S,M,L	\N	https://reputation-studios.com/products/sakura-flare-denim-light-stone	2024-12-09 08:23:44.868539	\N	\N	\N	125.00
125	\N	pants	133,116,100	Casual	Male	S,M,L,XL	\N	https://mnml.la/products/mnml-bottoms-bootcut-cargo-pants-m2020-p886-olv?nosto=frontpage-nosto-4-copy-1731688198721	2024-12-09 08:24:34.147821	\N	\N	\N	64.00
126	\N	pants	160,163,165	Casual	Male	S,M,L,XL	\N	https://mnml.la/products/mnml-denim-v709-wide-bellow-cargo-denim-m2024-d897-blu	2024-12-09 08:25:17.820959	\N	\N	\N	93.00
127	\N	shirt	168,179,197	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/smiley-big-apple-crewneck	2024-12-09 08:26:28.960136	\N	\N	\N	113.00
128	\N	shirt	189,114,83	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/smiley-good-game-t-shirt	2024-12-09 08:27:32.67973	\N	\N	\N	54.00
129	\N	shirt	202,145,148	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/smiley-good-game-t-shirt	2024-12-09 08:28:20.004448	\N	\N	\N	54.00
130	\N	shirt	70,81,103	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/smiley-celebration-t-shirt	2024-12-09 08:29:24.011486	\N	\N	\N	54.00
131	\N	shirt	34,30,36	Casual	Male	S,M,L,XL	\N	https://marketstudios.com/products/beware-sign-t-shirt	2024-12-09 08:29:59.07813	\N	\N	\N	54.00
132	\N	pants	132,123,119	Casual	Male	S,M,L,XL	\N	https://mnml.la/products/mnml-bottoms-paneled-blanket-pants-m2022-p570-mul?srsltid=AfmBOop6OW50FnUbYz14Zit02GFwL1JozwewQDP472R3ibDin_cszWOZ	2024-12-09 08:34:42.69934	\N	\N	\N	105.00
133	\N	shirt	188,151,114	Casual	Male	S,M,L,XL	user_images/shirt_04d0df51-1659-4414-a0c0-cfc7f6cc2224.png	https://www.jackjones.com/en-us/product/12263521_1957/oversized-fit-crew-neck-t-shirt	2024-12-11 05:01:35.846626	\N	\N	\N	25.00
134	\N	shirt	197,204,196	Casual	Male	S,M,L,XL	user_images/shirt_58350e37-f35f-49b4-aba6-e96cc92e267b.png	https://www.jackjones.com/en-us/product/12263521_3/oversized-fit-crew-neck-t-shirt	2024-12-11 05:02:07.487382	\N	\N	\N	25.00
135	\N	shirt	236,228,214	Casual	Male	S,M,L,XL	user_images/shirt_b28e213a-fa1a-4e7d-ac1b-33e452716339.png	https://www.jackjones.com/en-us/pro duct/12282604_4162/relaxed-fit-crew-neck-t-shirt	2024-12-11 05:02:55.658487	\N	\N	\N	30.00
136	\N	shirt	229,230,235	Casual	Male	S,M,L,XL	user_images/shirt_81753ff5-1c22-43dc-b456-fe3ecda4fd2f.png	https://www.jackjones.com/en-us/product/12262506_5/wide-fit-crew-neck-t-shirt	2024-12-11 05:03:42.853103	\N	\N	\N	25.00
137	\N	shirt	39,38,43	Casual	Male	S,M,L,XL	user_images/shirt_5bb23afe-fb29-4e54-a7ca-2d094a368124.png	https://www.jackjones.com/en-us/product/12262506_2161/wide-fit-crew-neck-t-shirt	2024-12-11 05:04:11.519772	\N	\N	\N	25.00
138	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	user_images/shirt_7a67182b-ebb6-4811-8ace-61889c835394.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/roses-tee-blac	2024-12-11 05:05:26.084879	\N	\N	\N	20.00
139	\N	shirt	189,169,54	Casual	Male	S,M,L,XL	user_images/shirt_ec0fe765-6c13-4e4e-a364-afab8464e985.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/test-your-luck-tee-natural	2024-12-11 05:07:34.136239	\N	\N	\N	27.99
140	\N	shirt	63,53,41	Casual	Male	S,M,L,XL	user_images/shirt_926a9474-8d9e-4329-a1bf-5b2842480536.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/limited-edition-tee-dark-chocolate	2024-12-11 05:08:01.112711	\N	\N	\N	27.99
141	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	user_images/shirt_9c07a264-cb1f-4226-95eb-2d0754982823.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/marathon-tee-black	2024-12-11 05:08:32.844516	\N	\N	\N	27.99
142	\N	shirt	226,224,231	Casual	Male	S,M,L,XL	user_images/shirt_f619d3fb-7e0b-4856-984e-cd8cf388512f.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/problem-child-tee-white	2024-12-11 05:10:21.576884	\N	\N	\N	27.99
143	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	user_images/shirt_0dd5efdc-098f-461d-96b2-161e8c2e76cc.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/eye-of-the-storm-tee-natural	2024-12-11 05:10:52.610919	\N	\N	\N	27.99
144	\N	shirt	151,146,140	Casual	Male	S,M,L,XL	user_images/shirt_455c4595-85e6-468a-b011-beba67d9138f.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/call-my-manager-tee-brown	2024-12-11 05:11:46.354238	\N	\N	\N	16.99
145	\N	shirt	33,68,127	Casual	Male	S,M,L,XL	user_images/shirt_9a94ca1b-4297-4479-863c-e72e4f3a0497.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/better-as-one-tee-heather-grey	2024-12-11 05:12:28.916236	\N	\N	\N	20.00
146	\N	shirt	203,222,217	Casual	Male	S,M,L	user_images/shirt_256fc997-f645-418b-99e5-54a3b1e9b8c8.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/lifes-a-trip-tee-forest-green	2024-12-11 05:23:16.201403	\N	\N	\N	20.00
147	\N	shirt	189,214,221	Casual	Male	S,M,L	user_images/shirt_4434a5f7-7b46-4639-9320-341aa0240953.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/world-tour-tee-light-blue	2024-12-11 05:24:19.991872	\N	\N	\N	27.99
148	\N	shirt	225,225,223	Casual	Male	S,M,L	user_images/shirt_c01286e0-4ede-4bf2-b6f5-73d9a448c1e0.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/cracked-tee-white	2024-12-11 05:25:05.370103	\N	\N	\N	27.99
149	\N	shirt	188,151,114	Casual	Male	S,M,L,XL	user_images/shirt_8281f257-11d1-4af5-9218-3aafd2a139f0.png	https://www.jackjones.com/en-us/product/12263521_1957/oversized-fit-crew-neck-t-shirt	2024-12-14 18:32:58.31492	\N	\N	\N	25.00
150	\N	shirt	197,204,196	Casual	Male	S,M,L,XL	user_images/shirt_d24bd054-a579-461d-b69e-0104b6ce8702.png	https://www.jackjones.com/en-us/product/12263521_3/oversized-fit-crew-neck-t-shirt	2024-12-14 18:34:37.844567	\N	\N	\N	30.00
151	\N	shirt	236,228,214	Casual	Male	S,M,L,XL	user_images/shirt_0076e1d1-e2fd-4faf-8ada-d8db35bd65cd.png	https://www.jackjones.com/en-us/product/12262506_5/wide-fit-crew-neck-t-shirt	2024-12-17 02:23:54.823897	\N	\N	\N	25.00
152	\N	shirt	229,230,235	Casual	Male	S,M,L,XL	user_images/shirt_d0b61f8f-32d8-4f28-8d7b-05ab9ceb736e.png	https://www.jackjones.com/en-us/product/12262506_2161/wide-fit-crew-neck-t-shirt	2024-12-17 02:26:35.229869	\N	\N	\N	25.00
153	\N	shirt	39,38,43	Casual	Male	S,M,L,XL	user_images/shirt_70a2c32e-2287-479b-92bc-cc4f1025043a.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/roses-tee-blac	2024-12-17 02:27:39.308776	\N	\N	\N	20.00
154	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	user_images/shirt_ead27d24-360a-4e58-85a0-a1a1bc255f7e.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/roses-tee-blac	2024-12-17 02:28:54.225888	\N	\N	\N	20.00
155	\N	shirt	189,169,54	Casual	Male	S,M,L,XL	user_images/shirt_3a1d8167-f0c1-40fd-b8bc-8a4f7158484d.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/test-your-luck-tee-natural	2024-12-17 02:29:39.105464	\N	\N	\N	27.99
156	\N	shirt	63,53,41	Casual	Male	S,M,L,XL	user_images/shirt_918b7e2f-cab9-4e3a-9546-071e1140f60d.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/limited-edition-tee-dark-chocolate	2024-12-17 02:30:17.297989	\N	\N	\N	27.99
157	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	user_images/shirt_d32b6aef-d04e-4da0-9686-c21e9bc69efc.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/marathon-tee-black	2024-12-17 02:31:02.541807	\N	\N	\N	27.99
158	\N	shirt	226,224,231	Casual	Male	S,M,L,XL	user_images/shirt_fdad92d8-ae79-48ed-96f8-7c034a7a945a.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/problem-child-tee-white	2024-12-17 02:31:37.226774	\N	\N	\N	27.99
159	\N	shirt	24,24,24	Casual	Male	S,M,L,XL	user_images/shirt_f917cb54-0da9-48a3-88c5-19928cd2c7c5.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/eye-of-the-storm-tee-natural	2024-12-17 02:32:15.682249	\N	\N	\N	27.99
160	\N	shirt	151,146,140	Casual	Male	S,M,L,XL	user_images/shirt_57901e93-d1c1-48c0-8c7a-d3dc8a141374.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/call-my-manager-tee-brown	2024-12-17 02:33:32.769174	\N	\N	\N	16.99
161	\N	shirt	33,68,127	Casual	Male	S,M,L,XL	user_images/shirt_6d7a51b4-af52-4944-ac47-0fa608bdf504.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/better-as-one-tee-heather-grey	2024-12-17 02:34:22.264684	\N	\N	\N	20.00
162	\N	shirt	203,222,217	Casual	Male	S,M,L,XL	user_images/shirt_87666d8e-6aaa-490e-a7c3-0d30e0c46efd.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/lifes-a-trip-tee-forest-green	2024-12-17 02:35:18.610068	\N	\N	\N	20.00
163	\N	shirt	111,152,217	Casual	Male	S,M,L,XL	user_images/shirt_8e19fb6e-a102-4997-b82b-67a64981f5ee.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/explore-tee-white	2024-12-17 02:36:33.122413	\N	\N	\N	27.99
164	\N	shirt	189,214,221	Casual	Male	S,M,L,XL	user_images/shirt_be6f68ed-a0cd-4659-9d87-9e938dccc9e0.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/world-tour-tee-light-blue	2024-12-17 02:37:06.64847	\N	\N	\N	27.99
165	\N	shirt	225,225,223	Casual	Male	S,M,L,XL	user_images/shirt_40f8bebe-7f81-47f1-af99-689ae6caf653.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/cracked-tee-white	2024-12-17 02:37:45.136471	\N	\N	\N	27.99
166	\N	shirt	224,225,228	Casual	Male	S,M,L,XL	user_images/shirt_3b96b24f-1d31-4208-a6f3-872387c053e0.png	https://www.youngandreckless.com/collections/mens-tops-graphic-tees/products/flower-district-tee-white	2024-12-17 02:38:29.642025	\N	\N	\N	20.00
167	\N	shirt	172,129,101	Casual	Male	S,M,L,XL	user_images/shirt_5d0a3329-9b86-49ca-a366-22addfa9a394.png	https://marketstudios.com/products/dog-will-hunt-t-shirt-2	2024-12-18 01:07:08.662562	\N	\N	\N	38.00
169	\N	shirt	248,134,81	Casual	Male	S,M,L,XL	user_images/shirt_c3eecb31-96ed-4c55-859c-68d1bd32a74d.png	https://marketstudios.com/products/bullrider-t-shirt-2	2024-12-18 01:08:34.524068	\N	\N	\N	38.00
170	\N	pants	170,163,149	Casual	Male	S,M,L,XL	user_images/pants_60e12fc8-c622-4b4c-b7ca-cb5df8a6151e.png	https://mnml.la/products/mnml-denim-d152-cargo-denim-m2022-d617-bro	2024-12-18 01:09:19.276487	\N	\N	\N	81.00
171	\N	pants	165,167,160	Casual	Male	S,M,L,XL	user_images/pants_058487c0-c9cb-480b-9061-f976c8793f52.png	https://mnml.la/products/mnml-denim-x511-denim-m2023-d884-blu	2024-12-18 01:10:04.205742	\N	\N	\N	76.00
172	\N	pants	186,185,183	Casual	Male	S,M,L,XL	user_images/pants_3198c86b-1bae-409a-a905-0f5f04646542.png	https://mnml.la/pr