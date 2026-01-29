const summaryCards = [
  { label: 'Active Customers', value: '128' },
  { label: 'Pending Validations', value: '12' },
  { label: 'Recent Data Logs', value: '342' },
];

const recentCustomers = [
  {
    name: 'Avery Stone',
    email: 'avery.stone@example.com',
    location: 'Seattle, WA',
    status: 'Active',
  },
  {
    name: 'Jordan Lee',
    email: 'jordan.lee@example.com',
    location: 'Toronto, ON',
    status: 'Needs Review',
  },
  {
    name: 'Priya Nair',
    email: 'priya.nair@example.com',
    location: 'London, UK',
    status: 'Active',
  },
];

export default function App() {
  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">AWS Lambda + Aurora Postgres</p>
          <h1>Customer Management</h1>
          <p className="subtitle">
            Track customer profiles, addresses, opt-ins, and data logs while enforcing
            validation and soft-delete workflows.
          </p>
        </div>
        <div className="actions">
          <button className="primary">Add customer</button>
          <button className="secondary">Import CSV</button>
        </div>
      </header>

      <section className="summary-grid">
        {summaryCards.map((card) => (
          <article key={card.label} className="summary-card">
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="content-grid">
        <article className="panel">
          <h2>Recent customers</h2>
          <div className="list">
            {recentCustomers.map((customer) => (
              <div key={customer.email} className="list-row">
                <div>
                  <p className="name">{customer.name}</p>
                  <p className="meta">{customer.email}</p>
                </div>
                <div>
                  <p className="meta">{customer.location}</p>
                  <p className={`status ${customer.status === 'Active' ? 'active' : 'review'}`}>
                    {customer.status}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Validation checklist</h2>
          <ul className="checklist">
            <li>First name, last name, and email address required.</li>
            <li>Latitude/longitude limited to -180 and 180.</li>
            <li>Soft deletes enabled via IsActive.</li>
            <li>All CRUD events logged to DataLog.</li>
          </ul>
        </article>
      </section>
    </div>
  );
}
