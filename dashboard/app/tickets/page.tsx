import { tickets } from "../../lib/data";

export default function TicketsPage() {
  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Support Tickets</h2>
        <p>
          Telegram support flows land here. Bugs and claims should be handled first, while ideas
          and improvements can move into a weekly review queue.
        </p>
      </section>

      <section className="panel">
        <h3>Queue</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Status</th>
              <th>User</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket, index) => (
              <tr key={`${ticket.user}-${index}`}>
                <td>{ticket.type}</td>
                <td>{ticket.status}</td>
                <td>{ticket.user}</td>
                <td>{ticket.body}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
