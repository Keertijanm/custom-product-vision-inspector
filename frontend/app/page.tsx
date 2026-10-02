import Link from "next/link";

export default function Home() {
  return (
    <div className="stacked-layout">
      <section className="panel hero-panel">
        <div>
          <p className="eyebrow">Custom product inspection</p>
          <h1>Configure an AI inspection workflow for real product checks.</h1>
          <p className="muted-text">
            Inspect packaging, labels, closures, logos, and defects with a clear pass/fail workflow designed for product QA and rapid verification.
          </p>
          <div className="action-row">
            <Link href="/setup" className="primary-button">
              Start inspection
            </Link>
            <Link href="/results" className="secondary-button text-button">
              View results
            </Link>
          </div>
        </div>
      </section>

      <section className="panel feature-grid">
        <div className="feature-card">
          <span className="metric-label">Fast setup</span>
          <h3>Define product-specific rules</h3>
          <p>Capture product identity, categories, and configurable inspection requirements for each inspection.</p>
        </div>
        <div className="feature-card">
          <span className="metric-label">AI review</span>
          <h3>Run validation against visual evidence</h3>
          <p>Trigger the inspection engine, review detections, and prioritize required product checks.</p>
        </div>
        <div className="feature-card">
          <span className="metric-label">Clear reporting</span>
          <h3>Explain each result with confidence</h3>
          <p>Display pass/fail reasoning for each check and retain the original image and evidence.</p>
        </div>
      </section>

      <section className="panel summary-grid">
        <div>
          <p className="eyebrow">Recent inspections</p>
          <ul className="recent-list">
            <li>
              <strong>Beverage Bottle</strong>
              <span>Passed · 94% confidence</span>
            </li>
            <li>
              <strong>Supplement Jar</strong>
              <span>Failed · Label missing</span>
            </li>
            <li>
              <strong>Electronics Box</strong>
              <span>Passed · 90% confidence</span>
            </li>
          </ul>
        </div>

        <div className="stat-card-wrap">
          <div className="stat-card">
            <span>Configurable checks</span>
            <strong>5</strong>
          </div>
          <div className="stat-card">
            <span>Inspection modes</span>
            <strong>3</strong>
          </div>
          <div className="stat-card">
            <span>Pass rate</span>
            <strong>92%</strong>
          </div>
        </div>
      </section>
    </div>
  );
}
