import { revalidatePath } from "next/cache";
import { invoiceTemplates } from "@invoicebot/shared";
import { prisma } from "../../lib/prisma";

type AdminUserRow = {
  id: string;
  name: string;
  handle: string;
  plan: string;
  invoiceCount: number;
  voiceCount: number;
  joinedAt: string;
  templateId: string;
  stripeCustomerId: string | null;
};

async function loadUsers(): Promise<AdminUserRow[]> {
  try {
    const rows = await prisma.$queryRaw<AdminUserRow[]>`
      SELECT
        u.id,
        COALESCE(NULLIF(TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))), ''), COALESCE(p.company_name, 'Unknown user')) AS name,
        COALESCE(u.telegram_handle, 'No handle') AS handle,
        u.plan_tier AS plan,
        u.invoice_count_this_month AS "invoiceCount",
        COALESCE(u.voice_transcriptions_this_month, 0) AS "voiceCount",
        TO_CHAR(u.joined_at, 'YYYY-MM-DD') AS "joinedAt",
        COALESCE(p.default_template_id, 'classic-blue') AS "templateId",
        u.stripe_customer_id AS "stripeCustomerId"
      FROM users u
      LEFT JOIN profiles p ON p.user_id = u.id
      ORDER BY u.joined_at DESC
    `;
    return rows;
  } catch {
    return [];
  }
}

async function resetVoiceUsage(formData: FormData) {
  "use server";

  const userId = String(formData.get("userId") ?? "");
  if (!userId) {
    return;
  }

  await prisma.$executeRaw`
    UPDATE users
    SET voice_transcriptions_this_month = 0,
        updated_at = NOW()
    WHERE id = ${userId}
  `;
  revalidatePath("/users");
}

async function resetInvoiceCount(formData: FormData) {
  "use server";

  const userId = String(formData.get("userId") ?? "");
  if (!userId) {
    return;
  }

  await prisma.$executeRaw`
    UPDATE users
    SET invoice_count_this_month = 0,
        updated_at = NOW()
    WHERE id = ${userId}
  `;
  revalidatePath("/users");
}

export default async function UsersPage() {
  const users = await loadUsers();
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
              <th>Voice</th>
              <th>Template</th>
              <th>Stripe</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={8}>No users found yet.</td>
              </tr>
            ) : users.map((user) => {
              const template = invoiceTemplates.find((item) => item.id === user.templateId);
              return (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.handle}</td>
                  <td>{user.plan}</td>
                  <td>{user.invoiceCount}</td>
                  <td>{user.voiceCount}</td>
                  <td>{template?.name ?? user.templateId}</td>
                  <td>{user.stripeCustomerId ?? "Not linked"}</td>
                  <td>
                    <div className="row-actions">
                      <form action={resetVoiceUsage}>
                        <input type="hidden" name="userId" value={user.id} />
                        <button className="button small-button" type="submit">Reset Voice</button>
                      </form>
                      <form action={resetInvoiceCount}>
                        <input type="hidden" name="userId" value={user.id} />
                        <button className="button small-button" type="submit">Reset Invoices</button>
                      </form>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
