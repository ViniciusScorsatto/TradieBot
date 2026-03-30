import { randomUUID } from "crypto";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { ActionButton } from "../../../components/action-button";
import { prisma } from "../../../lib/prisma";
import { sendTelegramMessage } from "../../../lib/telegram";

export const dynamic = "force-dynamic";

type TicketListRow = {
  id: string;
  type: "BUG" | "CLAIM" | "IMPROVEMENT" | "IDEA";
  status: "OPEN" | "IN_PROGRESS" | "CLOSED";
  subject: string;
  userName: string;
  handle: string;
  telegramUserId: string;
  latestMessage: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
};

type TicketMessageRow = {
  id: string;
  sender: string;
  body: string;
  createdAt: string;
};

async function loadTickets(): Promise<TicketListRow[]> {
  try {
    return await prisma.$queryRaw<TicketListRow[]>`
      SELECT
        t.id,
        t.type,
        t.status,
        t.subject,
        COALESCE(NULLIF(TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))), ''), COALESCE(p.company_name, 'Unknown business')) AS "userName",
        COALESCE(u.telegram_handle, 'No handle') AS handle,
        u.telegram_user_id AS "telegramUserId",
        COALESCE(last_message.body, 'No message yet') AS "latestMessage",
        TO_CHAR(t.created_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI') AS "createdAt",
        TO_CHAR(t.updated_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI') AS "updatedAt",
        COALESCE(message_count.count, 0)::int AS "messageCount"
      FROM tickets t
      JOIN users u ON u.id = t.user_id
      LEFT JOIN profiles p ON p.user_id = u.id
      LEFT JOIN LATERAL (
        SELECT body
        FROM ticket_messages
        WHERE ticket_id = t.id
        ORDER BY created_at DESC
        LIMIT 1
      ) last_message ON TRUE
      LEFT JOIN LATERAL (
        SELECT COUNT(*) AS count
        FROM ticket_messages
        WHERE ticket_id = t.id
      ) message_count ON TRUE
      ORDER BY
        CASE t.status
          WHEN 'OPEN' THEN 0
          WHEN 'IN_PROGRESS' THEN 1
          ELSE 2
        END,
        CASE t.type
          WHEN 'BUG' THEN 0
          WHEN 'CLAIM' THEN 1
          WHEN 'IMPROVEMENT' THEN 2
          ELSE 3
        END,
        t.updated_at DESC
    `;
  } catch {
    return [];
  }
}

async function loadTicketMessages(ticketId: string): Promise<TicketMessageRow[]> {
  try {
    return await prisma.$queryRaw<TicketMessageRow[]>`
      SELECT
        id,
        sender,
        body,
        TO_CHAR(created_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI') AS "createdAt"
      FROM ticket_messages
      WHERE ticket_id = ${ticketId}
      ORDER BY created_at ASC
    `;
  } catch {
    return [];
  }
}

async function updateTicketStatus(formData: FormData) {
  "use server";

  const ticketId = String(formData.get("ticketId") ?? "");
  const nextStatus = String(formData.get("status") ?? "");
  if (!ticketId || !["OPEN", "IN_PROGRESS", "CLOSED"].includes(nextStatus)) {
    redirect("/tickets?message=Choose a valid status.");
  }

  await prisma.$executeRaw`
    UPDATE tickets
    SET status = ${nextStatus},
        updated_at = NOW()
    WHERE id = ${ticketId}
  `;

  revalidatePath("/tickets");
  redirect(`/tickets?ticket=${encodeURIComponent(ticketId)}&message=${encodeURIComponent(`Ticket marked ${nextStatus.replace("_", " ").toLowerCase()}.`)}`);
}

async function replyToTicket(formData: FormData) {
  "use server";

  const ticketId = String(formData.get("ticketId") ?? "");
  const replyBody = String(formData.get("replyBody") ?? "").trim();
  if (!ticketId || !replyBody) {
    redirect(`/tickets?ticket=${encodeURIComponent(ticketId)}&message=${encodeURIComponent("Write a reply before sending.")}`);
  }

  const ticketRows = await prisma.$queryRaw<{ id: string; subject: string; telegramUserId: string; userName: string }[]>`
    SELECT
      t.id,
      t.subject,
      u.telegram_user_id AS "telegramUserId",
      COALESCE(NULLIF(TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))), ''), COALESCE(p.company_name, 'customer')) AS "userName"
    FROM tickets t
    JOIN users u ON u.id = t.user_id
    LEFT JOIN profiles p ON p.user_id = u.id
    WHERE t.id = ${ticketId}
    LIMIT 1
  `;

  const ticket = ticketRows[0];
  if (!ticket) {
    redirect("/tickets?message=That ticket no longer exists.");
  }

  await prisma.$executeRaw`
    INSERT INTO ticket_messages (id, ticket_id, sender, body)
    VALUES (${randomUUID()}, ${ticketId}, ${"admin"}, ${replyBody})
  `;

  await prisma.$executeRaw`
    UPDATE tickets
    SET status = CASE WHEN status = 'OPEN' THEN 'IN_PROGRESS' ELSE status END,
        updated_at = NOW()
    WHERE id = ${ticketId}
  `;

  const delivered = await sendTelegramMessage(
    ticket.telegramUserId,
    `Support update on "${ticket.subject}"\n\n${replyBody}`
  );

  revalidatePath("/tickets");
  redirect(
    `/tickets?ticket=${encodeURIComponent(ticketId)}&message=${encodeURIComponent(
      delivered
        ? `Reply sent to ${ticket.userName} in Telegram.`
        : `Reply saved on the ticket, but Telegram delivery failed.`
    )}`
  );
}

function statusTone(status: TicketListRow["status"]) {
  if (status === "OPEN") {
    return "badge status-open";
  }
  if (status === "IN_PROGRESS") {
    return "badge status-progress";
  }
  return "badge status-closed";
}

function typeTone(type: TicketListRow["type"]) {
  if (type === "BUG") {
    return "badge ticket-bug";
  }
  if (type === "CLAIM") {
    return "badge ticket-claim";
  }
  if (type === "IMPROVEMENT") {
    return "badge ticket-improvement";
  }
  return "badge ticket-idea";
}

function senderLabel(sender: string) {
  if (sender === "admin") {
    return "Admin";
  }
  if (sender === "ai") {
    return "AI triage";
  }
  return "Customer";
}

export default async function TicketsPage({
  searchParams
}: {
  searchParams?: { message?: string; ticket?: string };
}) {
  const tickets = await loadTickets();
  const selectedTicketId =
    searchParams?.ticket && tickets.some((ticket) => ticket.id === searchParams.ticket)
      ? searchParams.ticket
      : tickets[0]?.id;
  const selectedTicket = tickets.find((ticket) => ticket.id === selectedTicketId) ?? null;
  const messages = selectedTicket ? await loadTicketMessages(selectedTicket.id) : [];
  const message = searchParams?.message;

  const openCount = tickets.filter((ticket) => ticket.status === "OPEN").length;
  const inProgressCount = tickets.filter((ticket) => ticket.status === "IN_PROGRESS").length;
  const closedCount = tickets.filter((ticket) => ticket.status === "CLOSED").length;
  const bugCount = tickets.filter((ticket) => ticket.type === "BUG").length;

  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Support tickets</h2>
        <p>
          Telegram support conversations land here. Bugs and claims should get the fastest turnaround,
          while improvements and ideas can still move with clear status and reply history.
        </p>
      </section>

      <section className="grid metrics">
        <article className="metric">
          <span>Open tickets</span>
          <strong>{openCount}</strong>
        </article>
        <article className="metric">
          <span>In progress</span>
          <strong>{inProgressCount}</strong>
        </article>
        <article className="metric">
          <span>Closed</span>
          <strong>{closedCount}</strong>
        </article>
        <article className="metric">
          <span>Bug pressure</span>
          <strong>{bugCount}</strong>
        </article>
      </section>

      {message ? (
        <section className="notice success-notice">
          {message}
        </section>
      ) : null}

      <section className="ticket-layout">
        <aside className="panel ticket-list-panel">
          <div className="ticket-panel-head">
            <div>
              <h3>Queue</h3>
              <p>Newest urgent work rises to the top. Pick any thread to respond.</p>
            </div>
            <span className="badge">{tickets.length} total</span>
          </div>

          {tickets.length === 0 ? (
            <p className="muted">No support tickets yet.</p>
          ) : (
            <div className="ticket-list">
              {tickets.map((ticket) => (
                <a
                  key={ticket.id}
                  href={`/tickets?ticket=${ticket.id}`}
                  className={`ticket-list-item${ticket.id === selectedTicketId ? " active" : ""}`}
                >
                  <div className="ticket-list-meta">
                    <span className={typeTone(ticket.type)}>{ticket.type.toLowerCase()}</span>
                    <span className={statusTone(ticket.status)}>
                      {ticket.status.replace("_", " ").toLowerCase()}
                    </span>
                  </div>
                  <strong>{ticket.subject}</strong>
                  <p>{ticket.userName}</p>
                  <p className="ticket-preview">{ticket.latestMessage}</p>
                  <div className="ticket-list-foot">
                    <span>{ticket.messageCount} messages</span>
                    <span>{ticket.updatedAt}</span>
                  </div>
                </a>
              ))}
            </div>
          )}
        </aside>

        <article className="panel ticket-thread-panel">
          {!selectedTicket ? (
            <>
              <h3>No ticket selected</h3>
              <p className="muted">Choose a ticket from the queue to see the thread and reply from admin.</p>
            </>
          ) : (
            <div className="ticket-thread">
              <div className="ticket-thread-head">
                <div className="stack compact-stack">
                  <div className="row-actions">
                    <span className={typeTone(selectedTicket.type)}>{selectedTicket.type.toLowerCase()}</span>
                    <span className={statusTone(selectedTicket.status)}>
                      {selectedTicket.status.replace("_", " ").toLowerCase()}
                    </span>
                  </div>
                  <h3>{selectedTicket.subject}</h3>
                  <p>
                    {selectedTicket.userName} · {selectedTicket.handle} · opened {selectedTicket.createdAt}
                  </p>
                </div>

                <form action={updateTicketStatus} className="ticket-status-form">
                  <input type="hidden" name="ticketId" value={selectedTicket.id} />
                  <select
                    name="status"
                    className="input ticket-select"
                    defaultValue={selectedTicket.status}
                    aria-label="Ticket status"
                  >
                    <option value="OPEN">Open</option>
                    <option value="IN_PROGRESS">In progress</option>
                    <option value="CLOSED">Closed</option>
                  </select>
                  <ActionButton label="Update status" />
                </form>
              </div>

              <div className="ticket-thread-messages">
                {messages.map((entry) => (
                  <div
                    key={entry.id}
                    className={`ticket-bubble ${
                      entry.sender === "admin"
                        ? "admin-bubble"
                        : entry.sender == "ai"
                          ? "ai-bubble"
                          : "user-bubble"
                    }`}
                  >
                    <div className="ticket-bubble-head">
                      <strong>{senderLabel(entry.sender)}</strong>
                      <span>{entry.createdAt}</span>
                    </div>
                    <p>{entry.body}</p>
                  </div>
                ))}
              </div>

              <form action={replyToTicket} className="ticket-reply-form">
                <input type="hidden" name="ticketId" value={selectedTicket.id} />
                <label className="action-label" htmlFor="replyBody">
                  Reply in Telegram
                </label>
                <textarea
                  id="replyBody"
                  name="replyBody"
                  className="input textarea"
                  rows={6}
                  placeholder="Write a support reply. It will be saved to the thread and sent to the customer in Telegram."
                  required
                />
                <div className="row-actions">
                  <ActionButton label="Send reply" />
                </div>
              </form>
            </div>
          )}
        </article>
      </section>
    </div>
  );
}
