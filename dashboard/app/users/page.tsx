import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { invoiceTemplates } from "@invoicebot/shared";
import { ActionButton } from "../../components/action-button";
import { prisma } from "../../lib/prisma";

type AdminUserRow = {
  id: string;
  name: string;
  handle: string;
  plan: string;
  invoiceCount: number;
  paidInvoiceCredits: number;
  voiceCount: number;
  paidVoiceCredits: number;
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
        COALESCE(u.paid_invoice_credits, 0) AS "paidInvoiceCredits",
        COALESCE(u.voice_transcriptions_this_month, 0) AS "voiceCount",
        COALESCE(u.paid_voice_credits, 0) AS "paidVoiceCredits",
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
  const userName = String(formData.get("userName") ?? "user");
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
  redirect(`/users?message=${encodeURIComponent(`Voice usage reset for ${userName}`)}`);
}

async function resetInvoiceCount(formData: FormData) {
  "use server";

  const userId = String(formData.get("userId") ?? "");
  const userName = String(formData.get("userName") ?? "user");
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
  redirect(`/users?message=${encodeURIComponent(`Invoice count reset for ${userName}`)}`);
}

export default async function UsersPage({
  searchParams
}: {
  searchParams?: { message?: string };
}) {
  const users = await loadUsers();
  const message = searchParams?.message;
  const freeInvoiceLimit = Number(process.env.FREE_INVOICE_LIMIT ?? "10");
  const paidInvoiceBlock = Number(process.env.PAID_INVOICE_BLOCK ?? "20");
  const freeVoiceLimit = Number(process.env.FREE_VOICE_TRANSCRIPTIONS_PER_MONTH ?? "20");
  const paidVoiceBlock = Number(process.env.PAID_VOICE_BLOCK ?? "100");
  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Users</h2>
        <p>
          Review usage, template choice, Stripe status, and where manual quota adjustments may
          be needed for claims or support recovery.
        </p>
        <p>
          Current environment: {freeInvoiceLimit} free invoices, +{paidInvoiceBlock} invoices per paid block,
          {freeVoiceLimit} free voice notes, +{paidVoiceBlock} voice notes per paid block.
        </p>
      </section>

      {message ? (
        <section className="notice success-notice">
          {message}
        </section>
      ) : null}

      <section className="panel">
        <h3>Tradie roster</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Handle</th>
              <th>Plan</th>
              <th>Invoices Used</th>
              <th>Invoices Left</th>
              <th>Voice Used</th>
              <th>Voice Left</th>
              <th>Template</th>
              <th>Stripe</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={10}>No users found yet.</td>
              </tr>
            ) : users.map((user) => {
              const template = invoiceTemplates.find((item) => item.id === user.templateId);
              const freeInvoicesLeft = Math.max(freeInvoiceLimit - user.invoiceCount, 0);
              const freeVoiceLeft = Math.max(freeVoiceLimit - user.voiceCount, 0);
              return (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.handle}</td>
                  <td>{user.plan}</td>
                  <td>{user.invoiceCount}</td>
                  <td>{freeInvoicesLeft} free left, {user.paidInvoiceCredits} paid</td>
                  <td>{user.voiceCount}</td>
                  <td>{freeVoiceLeft} free left, {user.paidVoiceCredits} paid</td>
                  <td>{template?.name ?? user.templateId}</td>
                  <td>{user.stripeCustomerId ?? "Not linked"}</td>
                  <td>
                    <div className="row-actions">
                      <form action={resetVoiceUsage}>
                        <input type="hidden" name="userId" value={user.id} />
                        <input type="hidden" name="userName" value={user.name} />
                        <ActionButton label="Reset Voice" />
                      </form>
                      <form action={resetInvoiceCount}>
                        <input type="hidden" name="userId" value={user.id} />
                        <input type="hidden" name="userName" value={user.name} />
                        <ActionButton label="Reset Invoices" />
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
