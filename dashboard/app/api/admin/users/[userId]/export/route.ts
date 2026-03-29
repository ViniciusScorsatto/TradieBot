import { NextRequest } from "next/server";
import { auth } from "../../../../../../lib/auth";
import { prisma } from "../../../../../../lib/prisma";

export async function GET(
  _request: NextRequest,
  { params }: { params: { userId: string } }
) {
  const session = await auth();
  if (!session?.user) {
    return new Response("Unauthorized", { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { id: params.userId },
    include: {
      profile: true,
      clients: true,
      invoiceDrafts: {
        include: {
          items: true,
          client: true,
        },
        orderBy: { createdAt: "desc" },
      },
      invoices: {
        include: {
          items: true,
          client: true,
        },
        orderBy: { createdAt: "desc" },
      },
      tickets: {
        include: {
          messages: {
            orderBy: { createdAt: "asc" },
          },
        },
        orderBy: { createdAt: "desc" },
      },
      payments: {
        orderBy: { createdAt: "desc" },
      },
      promotionPreferences: {
        orderBy: { category: "asc" },
      },
      promotionDeliveries: {
        include: {
          campaign: true,
        },
        orderBy: { createdAt: "desc" },
      },
    },
  });

  if (!user) {
    return new Response("User not found", { status: 404 });
  }

  const fileSafeId = user.telegramUserId ?? user.id;
  return new Response(JSON.stringify(user, null, 2), {
    status: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Disposition": `attachment; filename="user-export-${fileSafeId}.json"`,
      "Cache-Control": "no-store",
    },
  });
}
