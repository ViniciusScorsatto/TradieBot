export async function sendTelegramMessage(
  telegramUserId: string,
  text: string,
  options?: {
    buttonText?: string;
    buttonUrl?: string;
  }
) {
  const token = process.env.TELEGRAM_TOKEN;
  if (!token) {
    return false;
  }

  const replyMarkup =
    options?.buttonText && options?.buttonUrl
      ? {
          inline_keyboard: [[{ text: options.buttonText, url: options.buttonUrl }]]
        }
      : undefined;

  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      chat_id: telegramUserId,
      text,
      reply_markup: replyMarkup
    })
  });

  return response.ok;
}
