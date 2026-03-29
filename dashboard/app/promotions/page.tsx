import { randomUUID } from "crypto";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { promotionCategories } from "@invoicebot/shared";
import { ActionButton } from "../../components/action-button";
import { prisma } from "../../lib/prisma";
import { sendTelegramMessage } from "../../lib/telegram";

type PreferenceCountRow = {
  category: string;
  subscriberCount: number;
};

type CampaignRow = {
  id: string;
  category: string;
  title: string;
  status: string;
  createdAt: string;
  sentAt: string | null;
  sentCount: number;
  failedCount: number;
};

async function loadPreferenceCounts(): Promise<PreferenceCountRow[]> {
  try {
    return await prisma.$queryRaw<PreferenceCountRow[]>`
      SELECT
        pref.category AS category,
        COUNT(*)::int AS "subscriberCount"
      FROM promotion_preferences pref
      JOIN users u ON u.id = pref.user_id
      WHERE u.promotion_consent_at IS NOT NULL
        AND u.promotion_opt_out_at IS NULL
      GROUP BY pref.category
      ORDER BY pref.category ASC
    `;
  } catch {
    return [];
  }
}

async function loadRecentCampaigns(): Promise<CampaignRow[]> {
  try {
    return await prisma.$queryRaw<CampaignRow[]>`
      SELECT
        c.id,
        c.category,
        c.title,
        c.status,
        TO_CHAR(c.created_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI') AS "createdAt",
        CASE
          WHEN c.sent_at IS NULL THEN NULL
          ELSE TO_CHAR(c.sent_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI')
        END AS "sentAt",
        COALESCE(SUM(CASE WHEN d.status = 'SENT' THEN 1 ELSE 0 END), 0)::int AS "sentCount",
        COALESCE(SUM(CASE WHEN d.status = 'FAILED' THEN 1 ELSE 0 END), 0)::int AS "failedCount"
      FROM promotion_campaigns c
      LEFT JOIN promotion_deliveries d ON d.campaign_id = c.id
      GROUP BY c.id
      ORDER BY c.created_at DESC
      LIMIT 8
    `;
  } catch {
    return [];
  }
}

async function sendPromotionCampaign(formData: FormData) {
  "use server";

  const category = String(formData.get("category") ?? "");
  const title = String(formData.get("title") ?? "").trim();
  const body = String(formData.get("body") ?? "").trim();
  const affiliateUrl = String(formData.get("affiliateUrl") ?? "").trim();
  const validCategory = promotionCategories.find((item) => item.id === category);

  if (!validCategory || !title || !body || !affiliateUrl) {
    redirect("/promotions?message=Choose a category and complete every field before sending.");
  }

  const recipients = await prisma.$queryRaw<{ userId: string; telegramUserId: string }[]>`
    SELECT
      u.id AS "userId",
      u.telegram_user_id AS "telegramUserId"
    FROM promotion_preferences pref
    JOIN users u ON u.id = pref.user_id
    WHERE pref.category = ${category}
      AND u.promotion_consent_at IS NOT NULL
      AND u.promotion_opt_out_at IS NULL
    ORDER BY u.joined_at ASC
  `;

  const campaignId = randomUUID();
  const campaignStatus = recipients.length > 0 ? "SENT" : "NO_MATCH";

  await prisma.$executeRaw`
    INSERT INTO promotion_campaigns (
      id,
      category,
      title,
      body,
      affiliate_url,
      status,
      created_by,
      sent_at
    )
    VALUES (
      ${campaignId},
      ${category},
      ${title},
      ${body},
      ${affiliateUrl},
      ${campaignStatus},
      ${"admin"},
      ${recipients.length > 0 ? new Date() : null}
    )
  `;

  let sentCount = 0;
  for (const recipient of recipients) {
    const delivered = await sendTelegramMessage(
      recipient.telegramUserId,
      `${title}\n\n${body}\n\nYou are receiving this because you opted into ${validCategory.label.toLowerCase()} promotions in Telegram. You can unsubscribe at any time.`,
      {
        buttonText: "Open offer",
        buttonUrl: affiliateUrl,
        secondaryButtonText: "Unsubscribe",
        secondaryButtonCallbackData: "promo_unsubscribe_all",
      }
    );

    await prisma.$executeRaw`
      INSERT INTO promotion_deliveries (
        id,
        campaign_id,
        user_id,
        telegram_user_id,
        status,
        error_message,
        delivered_at
      )
      VALUES (
        ${randomUUID()},
        ${campaignId},
        ${recipient.userId},
        ${recipient.telegramUserId},
        ${delivered ? "SENT" : "FAILED"},
        ${delivered ? null : "Telegram delivery failed"},
        ${delivered ? new Date() : null}
      )
    `;

    if (delivered) {
      sentCount += 1;
    }
  }

  revalidatePath("/promotions");
  redirect(
    `/promotions?message=${encodeURIComponent(
      recipients.length > 0
        ? `Promotion sent to ${sentCount} opted-in users in ${validCategory.label}.`
        : `No users are currently opted into ${validCategory.label}.`
    )}`
  );
}

export default async function PromotionsPage({
  searchParams
}: {
  searchParams?: { message?: string };
}) {
  const message = searchParams?.message;
  const counts = await loadPreferenceCounts();
  const recentCampaigns = await loadRecentCampaigns();
  const countsByCategory = new Map(counts.map((item) => [item.category, item.subscriberCount]));

  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Affiliate promotions</h2>
        <p>
          Send targeted affiliate offers only to users who explicitly consented to Telegram promotions and opted into those promo types inside the bot.
          Every campaign includes a one-tap unsubscribe action.
        </p>
      </section>

      {message ? (
        <section className="notice success-notice">
          {message}
        </section>
      ) : null}

      <section className="grid metrics">
        {promotionCategories.map((category) => (
          <article key={category.id} className="metric">
            <span>{category.label}</span>
            <strong>{countsByCategory.get(category.id) ?? 0}</strong>
          </article>
        ))}
      </section>

      <section className="two-col">
        <article className="panel">
          <h3>Send a promotion</h3>
          <p>
            Users control these preferences inside Telegram with <code>/promotions</code>. Pick a category
            and only consented users who opted into that category will receive the affiliate offer.
          </p>

          <form action={sendPromotionCampaign} className="form">
            <select className="input" name="category" defaultValue="" required>
              <option value="" disabled>Select a promotion category</option>
              {promotionCategories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.label} ({countsByCategory.get(category.id) ?? 0} opted in)
                </option>
              ))}
            </select>
            <input className="input" name="title" placeholder="Offer title" maxLength={80} required />
            <textarea
              className="input textarea"
              name="body"
              rows={6}
              maxLength={600}
              placeholder="Offer summary for the Telegram message"
              required
            />
            <input className="input" name="affiliateUrl" type="url" placeholder="https://affiliate-link.example" required />
            <ActionButton label="Send promotion" />
          </form>
        </article>

        <article className="panel">
          <h3>Preference coverage</h3>
          <div className="ticket-overview-list">
            {promotionCategories.map((category) => (
              <article key={category.id} className="ticket-overview-item">
                <div className="ticket-overview-top">
                  <strong>{category.label}</strong>
                  <span className="badge">{countsByCategory.get(category.id) ?? 0} users</span>
                </div>
                <p>{category.description}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="panel">
        <h3>Recent campaigns</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Title</th>
              <th>Status</th>
              <th>Sent</th>
              <th>Failed</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {recentCampaigns.length === 0 ? (
              <tr>
                <td colSpan={6}>No promotions sent yet.</td>
              </tr>
            ) : recentCampaigns.map((campaign) => (
              <tr key={campaign.id}>
                <td>{promotionCategories.find((item) => item.id === campaign.category)?.label ?? campaign.category}</td>
                <td>{campaign.title}</td>
                <td>{campaign.status}</td>
                <td>{campaign.sentCount}</td>
                <td>{campaign.failedCount}</td>
                <td>{campaign.sentAt ?? campaign.createdAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
