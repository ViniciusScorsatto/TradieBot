export async function sendTelegramMessage(telegramUserId: string, text: string) {
  const token = process.env.TELEGRAM_TOKEN;
  if (!token) {
    return false;
  }

  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      chat_id: telegramUserId,
      text
    })
  });

  return response.ok;
}
