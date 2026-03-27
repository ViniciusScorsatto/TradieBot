import { invoiceTemplates } from "@invoicebot/shared";
import { users } from "../../lib/data";

export default function UsersPage() {
  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Users</h2>
        <p>
          Review usage, template choice, Stripe status, and where manual quota adjustments may
          be needed for claims or support recovery.
        </p>
      </section>

      <section className="panel">
        <h3>Tradie roster</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Handle</th>
              <th>Plan</th>
              <th>Invoices</th>
              <th>Template</th>
              <th>Stripe</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const template = invoiceTemplates.find((item) => item.id === user.templateId);
              return (
                <tr key={user.handle}>
                  <td>{user.name}</td>
                  <td>{user.handle}</td>
                  <td>{user.plan}</td>
                  <td>{user.invoiceCount}</td>
                  <td>{template?.name ?? user.templateId}</td>
                  <td>{user.stripeCustomerId ?? "Not linked"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
