"""
AMXL Canada DS — Weekly Dashboard (Streamlit Cloud version)
Data lives in the data/ folder — push updated CSVs to refresh.
"""
import streamlit as st
import pandas as pd
import datetime, csv, io
from pathlib import Path
from collections import defaultdict

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AMXL Canada DS Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Constants ──────────────────────────────────────────────────────────────────
CANADA_STATIONS = ['HYC2','HYE1','HYO1','HYV1','HYZ1','HYZ2']
STATION_CITY    = {'HYC2':'Calgary','HYE1':'Edmonton','HYO1':'Ottawa',
                   'HYV1':'Vancouver','HYZ1':'Toronto','HYZ2':'Toronto'}

DATA_DIR = Path(__file__).parent / 'data'
SVC_CSV  = DATA_DIR / 'service_time_station_weekly.csv'
STAR_CSV = DATA_DIR / 'star_rating_weekly.csv'
URR_CSV  = DATA_DIR / 'iaq_urr_raw.csv'
FB_CSV   = DATA_DIR / 'star_nfpr_raw.csv'

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size:2rem !important; }
  [data-testid="stMetricLabel"] { font-size:0.75rem !important; font-weight:700;
    text-transform:uppercase; letter-spacing:.5px; color:#6B7280; }
  .block-container { padding-top:1.5rem; }
  .section-hdr { background:#1A2F4B; color:#fff; padding:6px 14px; border-radius:6px;
    font-size:12px; font-weight:700; letter-spacing:.4px; text-transform:uppercase;
    margin-bottom:10px; }
  .update-banner { background:#EEF3F8; border-left:4px solid #FF6B00; padding:8px 14px;
    border-radius:0 6px 6px 0; font-size:12px; color:#1A2F4B; margin-bottom:12px; }
  .note-box { background:#FFF8E6; border-left:3px solid #FF8C00; padding:6px 12px;
    border-radius:0 4px 4px 0; font-size:11px; color:#9C6500; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

# ── Password gate ─────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get('authenticated'):
        return True
    st.markdown('### 🔒 AMXL Canada DS Dashboard')
    pw = st.text_input('Enter password', type='password', key='pw_input')
    if st.button('Login'):
        if pw == 'SanniSS':
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error('Incorrect password.')
    return False

if not check_password():
    st.stop()

# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_visuals(fp):
    if not Path(fp).exists():
        return {}
    visuals, cid, rows, hdr = {}, None, [], None
    with open(fp, encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\n')
            if line.startswith('# visual '):
                if cid and hdr: visuals[cid] = {'header':hdr,'rows':rows}
                cid, rows, hdr = line[9:].strip(), [], None
            elif not line.strip(): continue
            elif hdr is None: hdr = line.split(',')
            else:
                for row in csv.reader(io.StringIO(line)): rows.append(row)
    if cid and hdr: visuals[cid] = {'header':hdr,'rows':rows}
    return visuals

def week_to_date(label):
    try:
        yr, wk = int(str(label)[:4]), int(str(label)[5:])
        return datetime.date.fromisocalendar(yr, wk, 1)
    except: return None

def month_to_date(label):
    try: return datetime.date.fromisoformat(str(label)[:7] + '-01')
    except: return None

def rolling_cutoffs(period, c_start=None, c_end=None):
    today = datetime.date.today()
    if period == "Last 4 weeks":   return today - datetime.timedelta(weeks=4),   today
    if period == "Last 8 weeks":   return today - datetime.timedelta(weeks=8),   today
    if period == "Last 3 months":  return today - datetime.timedelta(days=91),   today
    if period == "Last 6 months":  return today - datetime.timedelta(days=183),  today
    if period == "Last 12 months": return today - datetime.timedelta(days=365),  today
    if period == "Custom range":   return c_start or today-datetime.timedelta(weeks=8), c_end or today
    return today - datetime.timedelta(weeks=8), today

# ── Color helpers ──────────────────────────────────────────────────────────────
def svc_color(val, seca):
    if pd.isna(val): return ''
    if seca == 'ROC':
        if val <= 7:  return 'background-color:#70AD47;color:#fff;font-weight:700'
        if val <= 8:  return 'background-color:#FF8C00;color:#fff;font-weight:700'
    else:
        if val <= 10: return 'background-color:#70AD47;color:#fff;font-weight:700'
        if val <= 11: return 'background-color:#FF8C00;color:#fff;font-weight:700'
    return 'background-color:#C00000;color:#fff;font-weight:700'

def star_color(val):
    if pd.isna(val): return ''
    if val >= 5:  return 'background-color:#00703C;color:#fff;font-weight:700'
    if val >= 4:  return 'background-color:#70AD47;color:#fff;font-weight:700'
    return 'background-color:#C00000;color:#fff;font-weight:700'

def urr_color(val):
    if pd.isna(val): return ''
    if val < 8:   return 'background-color:#00703C;color:#fff;font-weight:700'
    if val <= 10: return 'background-color:#FF8C00;color:#fff;font-weight:700'
    return 'background-color:#C00000;color:#fff;font-weight:700'

def fb_color(val):
    if pd.isna(val): return ''
    if val >= 5:  return 'background-color:#00703C;color:#fff;font-weight:700'
    if val >= 4:  return 'background-color:#70AD47;color:#fff;font-weight:700'
    if val >= 3:  return 'background-color:#FF8C00;color:#fff;font-weight:700'
    return 'background-color:#C00000;color:#fff;font-weight:700'

def vs_color(val):
    if pd.isna(val): return ''
    if val >= 0: return 'background-color:#C6EFCE;color:#276221;font-weight:700'
    return 'background-color:#FFC7CE;color:#9C0006;font-weight:700'

# ── Data loaders ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_service_time():
    svc = parse_visuals(SVC_CSV)
    rows = []
    for row in svc.get('9dfe57ee-5b38-403c-ba3e-abcf9254a0ee',{}).get('rows',[]):
        if len(row) < 6: continue
        s_dsp,seca,tgt,week,act,cnt = row[0],row[1],row[2],row[3],row[4],row[5]
        stn = s_dsp.split(' - ')[0]
        if stn not in CANADA_STATIONS: continue
        try:
            rows.append({'Station':stn,'City':STATION_CITY[stn],
                         'Metric':'ROC' if seca=='D:R' else 'DDU',
                         'Target':float(tgt),'Week':week,
                         'Actual':round(float(act),2),'Pkgs':int(cnt),
                         'WkDate':week_to_date(week)})
        except: pass
    return pd.DataFrame(rows)

@st.cache_data(show_spinner=False)
def load_star_rating():
    star = parse_visuals(STAR_CSV)
    rows = []
    for row in star.get('1116401c-d659-4ab3-be0e-909a99957b59',{}).get('rows',[]):
        if len(row) < 7: continue
        stn,week = row[0],row[1]
        if stn not in CANADA_STATIONS: continue
        try:
            rows.append({'Station':stn,'City':STATION_CITY[stn],'Week':week,
                         'Reviews':int(row[2]),'Avg Rating':round(float(row[3]),2),
                         '1-Star %':round(float(row[6])*100,1),'WkDate':week_to_date(week)})
        except: pass
    net = []
    for row in star.get('966cbc88-055e-41ed-921e-5a809ec1ba05',{}).get('rows',[]):
        if len(row) < 2: continue
        try: net.append({'Week':row[0],'Net Avg':round(float(row[2]),3),'Reviews':int(row[1]),'1-Star %':round(float(row[3])*100,1),'WkDate':week_to_date(row[0])})
        except: pass
    return pd.DataFrame(rows), pd.DataFrame(net)

@st.cache_data(show_spinner=False)
def load_urr():
    urr = parse_visuals(URR_CSV)
    stn_rows = []
    for row in urr.get('816734c8-24e3-4078-b44a-63724e94fd52',{}).get('rows',[]):
        if len(row)<5: continue
        stn=row[0]
        if stn not in CANADA_STATIONS: continue
        try: stn_rows.append({'Station':stn,'City':STATION_CITY[stn],
                               'Deliveries':int(row[2]),'Undeliverable':int(row[4]),
                               'URR %':round(float(row[3])*100,1)})
        except: pass
    trend = []
    for row in urr.get('6c758083-29e3-4355-ac73-a9be50e8ffd6',{}).get('rows',[]):
        if len(row)<4: continue
        try:
            trend.append({'Month':str(row[0])[:7],'URR %':round(float(row[1])*100,1),
                          'Deliveries':int(row[2]),'Undeliverable':int(row[3]),
                          'MoDate':month_to_date(row[0])})
        except: pass
    trend.sort(key=lambda r:r['Month'])
    dsp_rows = []
    for row in urr.get('800907bb-a12f-4240-b459-989e74962163',{}).get('rows',[]):
        if len(row)<5: continue
        dsp,stn=row[0],row[1]
        if stn not in CANADA_STATIONS: continue
        try: dsp_rows.append({'DSP':dsp,'Station':stn,'City':STATION_CITY[stn],
                               'Deliveries':int(row[2]),'Undeliverable':int(row[4]),
                               'URR %':round(float(row[3])*100,1)})
        except: pass
    return pd.DataFrame(stn_rows), pd.DataFrame(trend), pd.DataFrame(dsp_rows)

@st.cache_data(show_spinner=False)
def load_feedback():
    fb = parse_visuals(FB_CSV)
    comments = []
    for row in fb.get('e81a3f8d-9100-421c-80a5-edfffdf30e5b',{}).get('rows',[]):
        if len(row)<6: continue
        stn,dsp,svc,_,comment,rating = row[0],row[1],row[2],row[3],row[4],row[5]
        if stn not in CANADA_STATIONS or not comment.strip(): continue
        try: comments.append({'Station':stn,'City':STATION_CITY[stn],'DSP':dsp,
                               'Service':svc,'Stars':int(float(rating)),'Comment':comment})
        except: pass
    summary = []
    for row in fb.get('1c1c783c-265a-42bd-8e81-35a4127cbe66',{}).get('rows',[]):
        if len(row)<3: continue
        stn=row[0]
        if stn not in CANADA_STATIONS: continue
        try: summary.append({'Station':stn,'City':STATION_CITY[stn],
                              'Reviews':int(row[2]),'Avg Rating':round(float(row[1]),2),
                              '1-Star %':round(float(row[3])*100,1) if len(row)>3 else 0})
        except: pass
    return pd.DataFrame(comments), pd.DataFrame(summary)

# ── Data freshness ─────────────────────────────────────────────────────────────
def data_age():
    if SVC_CSV.exists():
        import os
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(SVC_CSV))
        return mtime.strftime('%Y-%m-%d %H:%M')
    return 'unknown'

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📦 AMXL Canada DS")
    st.caption("Weekly Performance Dashboard")
    st.divider()

    period = st.selectbox("📅 Rolling Period", [
        "Last 4 weeks","Last 8 weeks","Last 3 months",
        "Last 6 months","Last 12 months","Custom range"
    ], index=0)

    c_start = c_end = None
    if period == "Custom range":
        today = datetime.date.today()
        c_start = st.date_input("From", today - datetime.timedelta(weeks=8), max_value=today)
        c_end   = st.date_input("To",   today, max_value=today)

    start_dt, end_dt = rolling_cutoffs(period, c_start, c_end)
    st.caption(f"Showing: {start_dt.strftime('%b %d')} → {end_dt.strftime('%b %d, %Y')}")
    st.divider()

    st.markdown("**🏢 Stations**")
    sel_stations = st.multiselect(
        "Stations", CANADA_STATIONS, default=CANADA_STATIONS,
        format_func=lambda x: f"{x} — {STATION_CITY[x]}",
        label_visibility="collapsed"
    )
    if not sel_stations: sel_stations = CANADA_STATIONS

    st.divider()
    st.markdown("**📊 Service Metrics**")
    show_roc = st.checkbox("ROC", value=True)
    show_ddu = st.checkbox("DDU", value=True)
    sel_metrics = [m for m,v in [('ROC',show_roc),('DDU',show_ddu)] if v] or ['ROC','DDU']

    st.divider()
    st.info(f"📅 Data last updated:\n**{data_age()}**\n\nTo refresh: update the CSV files in the GitHub repo and push.")
    st.divider()
    st.caption("Thresholds:\nROC ≤7🟢 7–8🟠 >8🔴\nDDU ≤10🟢 10–11🟠 >11🔴\n5★🟢 4★🟩 ≤3★🔴\nURR <8%🟢 8–10%🟠 >10%🔴")

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
today  = datetime.date.today()
wk_lbl = f"{today.isocalendar()[0]}-{today.isocalendar()[1]:02d}"
st.markdown(
    f"## 📦 AMXL Canada DS &nbsp;<span style='background:#FF6B00;color:#fff;"
    f"border-radius:16px;padding:3px 14px;font-size:14px'>WK {wk_lbl}</span>",
    unsafe_allow_html=True
)
st.markdown(
    f'<div class="update-banner">📅 Period: <b>{period}</b> &nbsp;|&nbsp; '
    f'{start_dt.strftime("%b %d")} → {end_dt.strftime("%b %d, %Y")} &nbsp;|&nbsp; '
    f'Stations: {" · ".join(sel_stations)} &nbsp;|&nbsp; Data: {data_age()}</div>',
    unsafe_allow_html=True
)

# ══════════════════════════════════════════════════════════════════════════════
# LOAD & FILTER
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner("Loading data..."):
    df_svc_raw          = load_service_time()
    df_star_raw, df_net = load_star_rating()
    df_urr_stn, df_urr_trend, df_urr_dsp = load_urr()
    df_fb, df_fb_sum    = load_feedback()

if df_svc_raw.empty and df_star_raw.empty:
    st.error("No data found in data/ folder. Check that CSV files exist.")
    st.stop()

def fw(df):
    if df.empty or 'WkDate' not in df.columns: return df
    mask = (df['WkDate'] >= start_dt) & (df['WkDate'] <= end_dt)
    if 'Station' in df.columns: mask = mask & df['Station'].isin(sel_stations)
    return df[mask].copy()

def fm(df):
    if df.empty or 'MoDate' not in df.columns: return df
    return df[(df['MoDate'] >= start_dt) & (df['MoDate'] <= end_dt)].copy()

df_svc       = fw(df_svc_raw)
df_svc       = df_svc[df_svc['Metric'].isin(sel_metrics)] if not df_svc.empty else df_svc
df_star      = fw(df_star_raw)
df_net_f     = fw(df_net)
df_urr_f     = fm(df_urr_trend)
df_urr_s     = df_urr_stn[df_urr_stn['Station'].isin(sel_stations)].copy() if not df_urr_stn.empty else df_urr_stn
df_fb_f      = df_fb[df_fb['Station'].isin(sel_stations)].copy() if not df_fb.empty else df_fb

# ══════════════════════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════════════════════
k1,k2,k3,k4,k5,k6 = st.columns(6)

if not df_svc.empty:
    red_n = df_svc.apply(lambda r: (r['Metric']=='ROC' and r['Actual']>8) or
                                    (r['Metric']=='DDU' and r['Actual']>11), axis=1).sum()
    k1.metric("🔴 In Red (Svc)", f"{int(red_n)}", delta=f"{len(df_svc)-int(red_n)} green", delta_color="normal")
else: k1.metric("🔴 In Red (Svc)", "—")

if not df_star.empty:
    k2.metric("⭐ CA Avg Rating", f"{df_star['Avg Rating'].mean():.2f}")
else: k2.metric("⭐ CA Avg Rating", "—")

if not df_net_f.empty:
    k3.metric("🍁 CA Network Avg", f"{df_net_f['Net Avg'].mean():.3f}")
else: k3.metric("🍁 CA Network Avg", "—")

if not df_urr_s.empty:
    urr_ca  = round(df_urr_s['Undeliverable'].sum() / df_urr_s['Deliveries'].sum() * 100, 1) if df_urr_s['Deliveries'].sum() > 0 else 0
    urr_red = int(df_urr_s['URR %'].gt(10).sum())
    k4.metric("📦 URR CA", f"{urr_ca:.1f}%", delta=f"{urr_red} stations >10%", delta_color="inverse")
else: k4.metric("📦 URR CA", "—")

if not df_fb_f.empty:
    k5.metric("💬 Positive FB", f"{(df_fb_f['Stars']>=4).sum()}",
              delta=f"{(df_fb_f['Stars']<=2).sum()} complaints", delta_color="inverse")
else: k5.metric("💬 Positive FB", "—")

k6.metric("🏢 Stations", f"{len(sel_stations)}", delta=period)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5 = st.tabs(["⏱ Service Time","⭐ 5-Star Rating","📦 URR","💬 Customer Feedback","📈 MoM Service Time"])

# ── Service Time ──────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-hdr">ROC & DDU — Station Level</div>', unsafe_allow_html=True)
    if df_svc.empty:
        st.info("No data in this period. Try a wider rolling window.")
    else:
        disp = df_svc[['Station','City','Metric','Target','Week','Actual','Pkgs']].copy()
        disp.insert(disp.columns.get_loc('Week')+1, 'Date',
                    df_svc['WkDate'].apply(lambda d: d.strftime('%b %d, %Y') if pd.notna(d) else ''))
        disp['Delta'] = (disp['Actual'] - disp['Target']).round(2)

        def _svc(df):
            s = pd.DataFrame('', index=df.index, columns=df.columns)
            for i,r in df.iterrows():
                c = svc_color(r['Actual'], r['Metric'])
                s.at[i,'Actual'] = c; s.at[i,'Delta'] = c
            return s

        st.dataframe(
            disp.style.apply(_svc, axis=None).format({'Target':'{:.0f}','Actual':'{:.2f}','Delta':'{:+.2f}'}),
            use_container_width=True, hide_index=True, height=min(400, 36*len(disp)+38)
        )
        c1,c2,c3 = st.columns(3)
        c1.success("ROC ≤7 min / DDU ≤10 min")
        c2.warning("ROC 7–8 min / DDU 10–11 min")
        c3.error("ROC >8 min / DDU >11 min")

# ── 5-Star ────────────────────────────────────────────────────────────────────
with tab2:
    col_a, col_b = st.columns([2,1])
    with col_a:
        st.markdown('<div class="section-hdr">Canada — Weekly Summary</div>', unsafe_allow_html=True)
        if not df_star.empty:
            net_map = dict(zip(df_net['Week'], df_net['Net Avg'])) if not df_net.empty else {}
            df_star['Net Avg']    = df_star['Week'].map(net_map)
            df_star['vs Network'] = (df_star['Avg Rating'] - df_star['Net Avg']).round(3)
            def _star(df):
                s = pd.DataFrame('', index=df.index, columns=df.columns)
                for i,r in df.iterrows():
                    s.at[i,'Avg Rating']  = star_color(r['Avg Rating'])
                    s.at[i,'vs Network']  = vs_color(r.get('vs Network'))
                return s
            st.dataframe(
                df_star[['Station','City','Week','Reviews','Avg Rating','1-Star %','Net Avg','vs Network']]
                .style.apply(_star, axis=None)
                .format({'Avg Rating':'{:.2f}','1-Star %':'{:.1f}%','Net Avg':'{:.3f}','vs Network':'{:+.3f}'}),
                use_container_width=True, hide_index=True, height=min(400, 36*len(df_star)+38)
            )
        elif not df_net_f.empty:
            # Per-station data unavailable — show Canada weekly aggregate from network visual
            disp_ca = df_net_f[['Week','Net Avg']].copy()
            disp_ca.columns = ['Week','Canada Avg ★']
            # add reviews from df_net if available
            if 'Reviews' in df_net_f.columns:
                disp_ca['Reviews'] = df_net_f['Reviews'].values
            def _ca(df):
                s = pd.DataFrame('', index=df.index, columns=df.columns)
                for i,r in df.iterrows(): s.at[i,'Canada Avg ★'] = star_color(r['Canada Avg ★'])
                return s
            st.dataframe(
                disp_ca.style.apply(_ca, axis=None).format({'Canada Avg ★':'{:.3f}'}),
                use_container_width=True, hide_index=True
            )
            st.markdown('<div class="note-box">⚠ Station-level star breakdown not available in current data extract — showing Canada network weekly average.</div>', unsafe_allow_html=True)
        else:
            st.info("No data in this period.")

    with col_b:
        st.markdown('<div class="section-hdr">Network Trend</div>', unsafe_allow_html=True)
        if not df_net_f.empty:
            def _net(df):
                s = pd.DataFrame('', index=df.index, columns=df.columns)
                for i,r in df.iterrows(): s.at[i,'Net Avg'] = star_color(r['Net Avg'])
                return s
            st.dataframe(
                df_net_f[['Week','Net Avg']].style.apply(_net, axis=None).format({'Net Avg':'{:.3f}'}),
                use_container_width=True, hide_index=True
            )
            st.line_chart(df_net_f.set_index('Week')['Net Avg'], height=160)

    st.divider()
    st.markdown('<div class="section-hdr">Customer Comments</div>', unsafe_allow_html=True)
    df_star_comments = df_fb[df_fb["Station"].isin(sel_stations)].copy() if not df_fb.empty else df_fb
    if not df_star_comments.empty:
        sc1, sc2 = st.columns([1,3])
        star_filter = sc1.selectbox("Filter by rating ", ["All","5 only","4 and above","Complaints (1-2)"], key="star_comment_filter")
        comment_search = sc2.text_input("Search comments", placeholder="Search...", key="star_comment_search")
        d = df_star_comments.copy()
        if star_filter == "5 only":          d = d[d["Stars"]==5]
        elif star_filter == "4 and above":    d = d[d["Stars"]>=4]
        elif star_filter == "Complaints (1-2)": d = d[d["Stars"]<=2]
        if comment_search: d = d[d["Comment"].str.contains(comment_search, case=False, na=False)]
        def _fbc(df):
            s = pd.DataFrame("", index=df.index, columns=df.columns)
            for i,r in df.iterrows(): s.at[i,"Stars"] = fb_color(r["Stars"])
            return s
        st.caption(f"{len(d)} comment(s)")
        st.dataframe(
            d[["Station","City","DSP","Service","Stars","Comment"]].style.apply(_fbc, axis=None),
            use_container_width=True, hide_index=True,
            column_config={"Comment": st.column_config.TextColumn("Customer Comment", width="large")}
        )
    else:
        st.info("No customer comments available.")

# ── URR ───────────────────────────────────────────────────────────────────────
with tab3:
    c1, c2 = st.columns([1,1])
    with c1:
        st.markdown('<div class="section-hdr">By Station</div>', unsafe_allow_html=True)
        if not df_urr_s.empty:
            def _urr(df):
                s = pd.DataFrame('', index=df.index, columns=df.columns)
                for i,r in df.iterrows(): s.at[i,'URR %'] = urr_color(r['URR %'])
                return s
            st.dataframe(df_urr_s.style.apply(_urr, axis=None).format({'URR %':'{:.1f}%'}),
                         use_container_width=True, hide_index=True)
        else: st.info("No URR data.")

    with c2:
        st.markdown('<div class="section-hdr">URR % — Station Bar Chart</div>', unsafe_allow_html=True)
        if not df_urr_s.empty:
            chart_df = df_urr_s.set_index('Station')[['URR %']].sort_values('URR %', ascending=False)
            st.bar_chart(chart_df, height=220, color="#C00000")
        else: st.info("No URR data.")

    st.divider()
    st.markdown('<div class="section-hdr">By DSP</div>', unsafe_allow_html=True)
    df_urr_dsp_f = df_urr_dsp[df_urr_dsp["Station"].isin(sel_stations)].copy() if not df_urr_dsp.empty else df_urr_dsp
    if not df_urr_dsp_f.empty:
        df_urr_dsp_f = df_urr_dsp_f.sort_values("URR %", ascending=False)
        def _urrd(df):
            s = pd.DataFrame("", index=df.index, columns=df.columns)
            for i,r in df.iterrows(): s.at[i,"URR %"] = urr_color(r["URR %"])
            return s
        st.dataframe(df_urr_dsp_f.style.apply(_urrd, axis=None).format({"URR %":"{:.1f}%"}),
                     use_container_width=True, hide_index=True)
    else: st.info("No DSP-level URR data.")

    st.markdown('<div class="note-box">Thresholds: <b>&lt;8% Green</b> | <b>8-10% Orange</b> | <b>&gt;10% Red</b></div>',
                unsafe_allow_html=True)

# ── Customer Feedback ─────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-hdr">Station Summary (last ~4 months)</div>', unsafe_allow_html=True)
    if not df_fb_sum.empty:
        df_fbs = df_fb_sum[df_fb_sum['Station'].isin(sel_stations)].copy()
        def _fbs(df):
            s = pd.DataFrame('', index=df.index, columns=df.columns)
            for i,r in df.iterrows(): s.at[i,'Avg Rating'] = star_color(r['Avg Rating'])
            return s
        st.dataframe(
            df_fbs.style.apply(_fbs, axis=None).format({'Avg Rating':'{:.2f}','1-Star %':'{:.1f}%'}),
            use_container_width=True, hide_index=True
        )
    st.divider()

    f1, f2 = st.columns([1,3])
    star_f  = f1.selectbox("Filter by rating",
                            ["All","5★ only","4★ and above","Complaints only (≤2★)"])
    search  = f2.text_input("🔍 Search comments", placeholder="Search customer comments...")

    if not df_fb_f.empty:
        d = df_fb_f.copy()
        if star_f == "5★ only":                d = d[d['Stars']==5]
        elif star_f == "4★ and above":          d = d[d['Stars']>=4]
        elif star_f == "Complaints only (≤2★)": d = d[d['Stars']<=2]
        if search: d = d[d['Comment'].str.contains(search, case=False, na=False)]

        st.markdown(f'<div class="section-hdr">Comments — {len(d)} result(s)</div>',
                    unsafe_allow_html=True)

        def _fb(df):
            s = pd.DataFrame('', index=df.index, columns=df.columns)
            for i,r in df.iterrows(): s.at[i,'Stars'] = fb_color(r['Stars'])
            return s

        st.dataframe(
            d[['Station','City','DSP','Service','Stars','Comment']].style.apply(_fb, axis=None),
            use_container_width=True, hide_index=True,
            column_config={"Comment": st.column_config.TextColumn("Customer Comment", width="large")}
        )
    else:
        st.info("No feedback data available.")

# ── MoM Service Time ─────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-hdr">Month-over-Month — ROC & DDU Average Service Time</div>', unsafe_allow_html=True)

    MOM_CSV = DATA_DIR / 'mom_service_time_raw.csv'

    def parse_mom_csv(filepath):
        """Parse quicksuite multi-visual CSV for MoM service time data."""
        import csv as _csv
        try:
            text = Path(filepath).read_text(encoding='utf-8', errors='replace')
        except Exception:
            return pd.DataFrame()
        rows = []
        in_data = False
        headers = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('# visual'):
                in_data = False
                headers = None
                continue
            if not stripped:
                continue
            parsed = list(_csv.reader([stripped]))[0]
            if headers is None:
                headers = parsed
                in_data = True
                continue
            if in_data and len(parsed) >= max(3, len(headers)):
                row = dict(zip(headers, parsed))
                rows.append(row)
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    if not MOM_CSV.exists():
        st.info("MoM service time data not yet pulled. Run refresh to populate.")
        st.markdown("**Source:** Star Rating dashboard — contains per-delivery service time history (Apr–present)")
    else:
        try:
            df_mom_raw = parse_mom_csv(MOM_CSV)

            if df_mom_raw.empty:
                st.warning("MoM CSV parsed but returned no rows.")
            else:
                # Build per-delivery records
                # group_0=site, group_2=date, group_10=svc_code (D:R/U), group_17=service_time_sec
                df_mom = df_mom_raw[['group_0','group_2','group_10','group_11','group_17']].copy()
                df_mom.columns = ['Site','Date','SvcCode','SvcType','SvcTimeSec']
                df_mom['Site']       = df_mom['Site'].str.strip()
                df_mom['Date']       = pd.to_datetime(df_mom['Date'], errors='coerce')
                df_mom['SvcTimeSec'] = pd.to_numeric(df_mom['SvcTimeSec'], errors='coerce')
                df_mom['SvcTimeMin'] = df_mom['SvcTimeSec'] / 60
                df_mom['ServiceType'] = df_mom['SvcCode'].map({'D:R': 'ROC', 'U': 'DDU'}).fillna(df_mom['SvcType'])
                df_mom['Month']      = df_mom['Date'].dt.to_period('M').astype(str)
                df_mom = df_mom.dropna(subset=['Date','SvcTimeSec','Site'])
                df_mom = df_mom[df_mom['Site'].isin(CANADA_STATIONS)]

                # Monthly averages per site per service type
                df_agg = (df_mom.groupby(['Site','Month','ServiceType'])
                          .agg(AvgMin=('SvcTimeMin','mean'), Count=('SvcTimeMin','count'))
                          .reset_index())
                df_agg['AvgMin'] = df_agg['AvgMin'].round(2)
                df_agg['Threshold'] = df_agg['ServiceType'].map({'ROC': 7, 'DDU': 10})
                df_agg['Status'] = df_agg.apply(
                    lambda r: '🟢' if r['AvgMin'] <= r['Threshold'] else '🔴', axis=1)

                # Date range info
                months = sorted(df_agg['Month'].unique())
                st.caption(f"Period: {months[0]} → {months[-1]}  |  {len(months)} months  |  {len(df_mom):,} rated deliveries")

                # Filter controls
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    svc_filter = st.radio("Service Type", ['Both','ROC','DDU'], horizontal=True, key='mom_svc')
                with col_f2:
                    site_filter = st.multiselect("Sites", CANADA_STATIONS, default=CANADA_STATIONS, key='mom_sites')

                df_plot = df_agg[df_agg['Site'].isin(site_filter)]
                if svc_filter != 'Both':
                    df_plot = df_plot[df_plot['ServiceType'] == svc_filter]

                if df_plot.empty:
                    st.info("No data for selected filters.")
                else:
                    import plotly.express as px
                    import plotly.graph_objects as go

                    # ── Line chart per service type ───────────────────────────
                    for svc_type, threshold in [('ROC', 7), ('DDU', 10)]:
                        if svc_filter != 'Both' and svc_filter != svc_type:
                            continue
                        df_svc_plot = df_plot[df_plot['ServiceType'] == svc_type]
                        if df_svc_plot.empty:
                            continue

                        fig = px.line(
                            df_svc_plot.sort_values(['Site','Month']),
                            x='Month', y='AvgMin', color='Site',
                            markers=True,
                            title=f'{svc_type} — Monthly Avg Service Time (min) | Threshold: {threshold} min',
                            labels={'AvgMin': 'Avg Service Time (min)', 'Month': 'Month'},
                        )
                        fig.add_hline(
                            y=threshold, line_dash='dash', line_color='#ff4b4b',
                            annotation_text=f'Threshold {threshold} min',
                            annotation_position='top right'
                        )
                        fig.update_layout(
                            plot_bgcolor='#0e1117', paper_bgcolor='#1e1e2e',
                            font_color='#fafafa', height=380,
                            xaxis=dict(showgrid=False),
                            yaxis=dict(showgrid=True, gridcolor='#333', range=[0, threshold * 1.5]),
                            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    # ── Summary heatmap table ─────────────────────────────────
                    st.markdown("---")
                    st.markdown("**Monthly Averages — All Sites**")

                    for svc_type, threshold, color_over in [('ROC', 7, '#ff4b4b'), ('DDU', 10, '#ff4b4b')]:
                        if svc_filter != 'Both' and svc_filter != svc_type:
                            continue
                        df_tbl = df_plot[df_plot['ServiceType'] == svc_type].copy()
                        if df_tbl.empty:
                            continue

                        pivot = df_tbl.pivot_table(
                            index='Site', columns='Month', values='AvgMin', aggfunc='mean'
                        ).round(2).reindex(index=[s for s in CANADA_STATIONS if s in site_filter])

                        st.markdown(f"**{svc_type}** (threshold {threshold} min)")

                        def color_cell(val):
                            if pd.isna(val):
                                return 'background-color: #222; color: #555'
                            elif val > threshold:
                                return 'background-color: #ff4b4b; color: white; font-weight:bold'
                            elif val > threshold * 0.9:
                                return 'background-color: #ffa500; color: black'
                            else:
                                return 'background-color: #21c55d22; color: #21c55d'

                        styled = pivot.style.map(color_cell).format('{:.2f}', na_rep='—')
                        st.dataframe(styled, use_container_width=True)
                        st.markdown("")

        except Exception as e:
            import traceback
            st.error(f"MoM tab error: {e}")
            with st.expander("Details"):
                st.code(traceback.format_exc())
