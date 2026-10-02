import { useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { PublicHeader, PageHeader } from "../components/Layout";
import { useApi } from "../hooks/useApi";

const COPYRIGHT_YEAR = 2026;

function CentreCard({ centre }) {
  return <article className="centre-card"><div className={`centre-cover cover-${(centre.name?.length || 0) % 4}`}><span>✚</span><small>{centre.city}{centre.state ? `, ${centre.state}` : ""}</small></div><div className="centre-card-body"><div className="card-label"><span>DIAGNOSTIC CENTRE</span><span className="open-status"><i/> Open</span></div><h3>{centre.name}</h3><p>{centre.address}, {centre.city}</p><div className="service-chips">{(centre.services || []).slice(0, 3).map((service) => <span key={service}>{service}</span>)}</div><div className="card-bottom"><span>Verified centre</span><Link to={`/centres/${centre.id}`}>View details <b>↗</b></Link></div></div></article>;
}

function Home() {
  const {
    items: centres,
    loading: centresLoading,
    error: centresError,
  } = useApi("/centres?limit=3");
  const {
    items: tests,
    loading: testsLoading,
    error: testsError,
  } = useApi("/tests?limit=4");
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  return <><PublicHeader/><main>
    <section className="hero-section"><div className="hero-copy"><p className="eyebrow">CARE FOR YOUR WHOLE JOURNEY</p><h1>Your health.<br/><em>Our priority.</em></h1><p>Book diagnostic tests at trusted centres near you. Fast, reliable, and easy to fit into your day.</p><form className="hero-search" onSubmit={(e) => { e.preventDefault(); navigate(`/centres?q=${encodeURIComponent(search)}`); }}><span>⌕</span><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search tests, centres or locations…" aria-label="Search tests, centres or locations"/><button aria-label="Search">⌕</button></form><button className="location-button" onClick={() => { if (!navigator.geolocation) { navigate("/centres"); return; } navigator.geolocation.getCurrentPosition(({ coords }) => navigate(`/centres?lat=${coords.latitude}&lon=${coords.longitude}`), () => navigate("/centres")); }}>⌖ &nbsp; Use my location</button><div className="trust-points"><span>✚<small>Trusted centres</small></span><span>⚕<small>Wide range of tests</small></span><span>▣<small>Easy booking</small></span><span>♡<small>Secure payments</small></span></div></div><div className="hero-art"><div className="hero-glow"/><div className="hero-illustration"><div className="doctor-circle"><span>+</span><div className="doctor-head"/><div className="doctor-body"><i/><b/></div><div className="stethoscope">⌁</div></div><div className="hero-bubble"><b>♡</b><span>Better health<br/>brighter tomorrow</span></div></div><div className="hero-leaf leaf-one">✦</div><div className="hero-leaf leaf-two">✦</div></div></section>
    <section id="about" className="benefit-strip">{[["✚","Trusted centres"],["⌖","Care near you"],["▦","Simple booking"],["♡","Secure payments"]].map(([icon,label])=><div key={label}><span>{icon}</span><b>{label}</b></div>)}</section>
    <section className="public-section"><div className="section-title"><div><p className="eyebrow">CARE CLOSE TO HOME</p><h2>Find a diagnostic centre</h2></div><Link to="/centres" className="subtle-link">Explore all centres →</Link></div><div className="centre-grid">{centres.slice(0,3).map((c)=><CentreCard key={c.id} centre={c}/>)}</div>{centresLoading && <div className="empty-state" role="status">Loading diagnostic centres…</div>}{!centresLoading && centresError && <div className="notice error" role="alert">{centresError}</div>}{!centresLoading && !centresError && !centres.length && <div className="empty-state"><span>⌖</span><b>Centres will appear here once added by your care team.</b></div>}</section>
    <section className="public-section test-showcase"><div className="section-title"><div><p className="eyebrow">TEST CATALOGUE</p><h2>Tests that help you stay informed</h2></div><Link to="/tests" className="subtle-link">Browse all tests →</Link></div><div className="test-grid">{tests.slice(0,4).map((test)=><Link className="test-tile" to={`/tests?q=${encodeURIComponent(test.name)}`} key={test.id}><span className="test-icon">✚</span><div><small>{test.category || "DIAGNOSTICS"}</small><h3>{test.name}</h3><p>{test.description || test.preparation_instructions || "Explore available centres and pricing."}</p></div><b>↗</b></Link>)}</div>{testsLoading && <div className="empty-state" role="status">Loading the test catalogue…</div>}{!testsLoading && testsError && <div className="notice error" role="alert">{testsError}</div>}{!testsLoading && !testsError && !tests.length && <div className="empty-state"><b>No tests are available yet.</b></div>}<div className="cta-banner"><div><p className="eyebrow">A BETTER WAY TO BOOK</p><h2>Take the next step<br/>for your wellbeing.</h2><p>Choose a centre, pick your test, and reserve a time that works for you.</p></div><Link className="primary-button" to="/centres">Get started <span>→</span></Link><div className="cta-symbol">♡</div></div></section>
    <footer id="contact" className="site-footer"><Link className="brand" to="/">♡ <b>EVE Healthcare</b></Link><span>Thoughtful care, every day.</span><span>© {COPYRIGHT_YEAR} EVE Healthcare</span></footer>
  </main></>;
}

export function CentresPage() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const [city, setCity] = useState(params.get("city") || "");
  const nearby = params.get("lat") && params.get("lon");
  const path = useMemo(() => nearby ? `/centres/nearby?latitude=${params.get("lat")}&longitude=${params.get("lon")}&radius_km=25` : `/centres?${new URLSearchParams({ ...(q ? { q } : {}), ...(city ? { city } : {}), limit: "50" })}`, [nearby, params, q, city]);
  const { items: centres, error, loading } = useApi(path);
  const clearNearby = () => { params.delete("lat"); params.delete("lon"); setParams(params); };
  const items = centres;
  return <><PublicHeader/><main className="public-page"><PageHeader eyebrow="OUR CARE NETWORK" title="Find a diagnostic centre" subtitle="Search by centre, city, or service. Location sharing is optional."/><form className="filter-bar" onSubmit={(e)=>e.preventDefault()}><label className="search-field">⌕<input value={q} onChange={(e)=>setQ(e.target.value)} placeholder="Centre name or service"/></label><label className="search-field">⌖<input value={city} onChange={(e)=>setCity(e.target.value)} placeholder="City"/></label>{nearby && <button className="outline-button" type="button" onClick={clearNearby}>Clear nearby search</button>}<button className="location-button compact" onClick={(e)=>{e.preventDefault();navigator.geolocation?.getCurrentPosition(({coords})=>setParams({lat:String(coords.latitude),lon:String(coords.longitude)}));}}>⌖ Find near me</button></form><div className="results-meta">{loading ? "Finding centres…" : `${items.length} centres found`}{error && <span className="form-error">{error}</span>}</div><div className="centre-grid">{centres.map((c)=><CentreCard key={c.id} centre={c}/>)}</div>{!loading && !centres.length && <div className="empty-state"><span>⌖</span><b>No centres match your search.</b><p>Try a different city or service, or browse without sharing your location.</p></div>}</main></>;
}

export function CentreDetailPage() {
  const { centreId } = useParams();
  const { data: centre, loading, error } = useApi(`/centres/${centreId}`);
  const { items: offers } = useApi(`/centre-tests?centre_id=${centreId}&limit=100`);
  const { items: tests } = useApi("/tests?limit=100");
  const testById = Object.fromEntries(tests.map((test) => [test.id, test]));
  if (loading) return <><PublicHeader/><main className="public-page">Loading centre details…</main></>;
  if (!centre) return <><PublicHeader/><main className="public-page"><div className="notice error">{error || "Centre not found."}</div></main></>;
  return <><PublicHeader/><main className="public-page"><Link className="subtle-link" to="/centres">← All centres</Link><div className="detail-hero"><div><p className="eyebrow">VERIFIED DIAGNOSTIC CENTRE</p><h1>{centre.name}</h1><p>{centre.address}, {centre.city}{centre.state ? `, ${centre.state}` : ""} {centre.postal_code || ""}</p><p>{centre.phone || ""} {centre.email ? `· ${centre.email}` : ""}</p></div><div className="detail-mark">✚</div></div><div className="detail-columns"><section className="panel"><p className="eyebrow">ABOUT THE CENTRE</p><h2>Care and services</h2><p>{centre.description || "This diagnostic centre provides accessible testing services through the EVE Healthcare network."}</p><div className="service-chips">{(centre.services || []).map((s)=><span key={s}>{s}</span>)}</div>{centre.opening_hours && <div className="hours-box"><b>Opening hours</b>{Object.entries(centre.opening_hours).map(([day,hours])=><p key={day}><span>{day}</span><span>{hours}</span></p>)}</div>}</section><section className="panel"><div className="section-title"><div><p className="eyebrow">AVAILABLE HERE</p><h2>Tests and pricing</h2></div></div>{offers.map((offer)=><article className="offer-row" key={offer.id}><div><h3>{testById[offer.test_id]?.name || "Diagnostic test"}</h3><p>{testById[offer.test_id]?.category || "Available test"} · {testById[offer.test_id]?.sample_type || "Sample details on request"}</p></div><strong>₹{Number(offer.price).toFixed(0)}</strong><Link className="primary-button" to={`/app/book?centre=${centre.id}&test=${offer.test_id}`}>Book</Link></article>)}{!offers.length && <p className="muted">No tests are currently listed. Please check back later.</p>}</section></div></main></>;
}

export function TestsPage() {
  const [q, setQ] = useState("");
  const [query, setQuery] = useState(new URLSearchParams(window.location.search).get("q") || "");
  const { items: tests, loading } = useApi(`/tests?${new URLSearchParams({ ...(query ? { q: query } : {}), limit: "100" })}`);
  return <><PublicHeader/><main className="public-page"><PageHeader eyebrow="TEST CATALOGUE" title="Understand your testing options" subtitle="Explore common diagnostic tests and the preparation information available."/><form className="filter-bar" onSubmit={(e)=>{e.preventDefault();setQuery(q);}}><label className="search-field">⌕<input value={q} onChange={(e)=>setQ(e.target.value)} placeholder="Search tests by name"/></label><button className="primary-button">Search tests</button></form>{loading ? <p>Loading tests…</p> : <div className="test-grid">{tests.map((test)=><article className="test-tile test-detail-tile" key={test.id}><span className="test-icon">✚</span><div><small>{test.category || "DIAGNOSTICS"}</small><h3>{test.name}</h3><p>{test.description || "Learn about available centres and book a test."}</p><div className="test-facts"><span>Sample: {test.sample_type || "Centre dependent"}</span><span>Report: {test.estimated_report_time_minutes ? `${test.estimated_report_time_minutes} min` : "Centre dependent"}</span></div><p className="prep-note"><b>Preparation:</b> {test.preparation_instructions || "Follow the instructions provided by the selected centre."}</p></div><Link className="text-button" to={`/centres`}>Find a centre →</Link></article>)}</div>}{!tests.length && <div className="empty-state"><b>No tests found.</b></div>}</main></>;
}

export default Home;
