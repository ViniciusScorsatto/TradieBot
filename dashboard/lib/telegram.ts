export async function sendTelegramMessage(
  telegramUserId: string,
  text: string,
  options?: {
    buttonText?: string;
    buttonUrl?: string;
    secondaryButtonText?: string;
    secondaryButtonCallbackData?: string;
  }
) {
  const token = process.env.TELEGRAM_TOKEN;
  if (!token) {
    return false;
  }

  const firstRow: Array<Record<string, string>> = [];
  if (options?.buttonText && options?.buttonUrl) {
    firstRow.push({ text: options.buttonText, url: options.buttonUrl });
  }
  if (options?.secondaryButtonText && options?.secondaryButtonCallbackData) {
    firstRow.push({ text: options.secondaryButtonText, callback_data: options.secondaryButtonCallbackData });
  }

  const replyMarkup = firstRow.length > 0 ? { inline_keyboard: [firstRow] } : undefined;

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
