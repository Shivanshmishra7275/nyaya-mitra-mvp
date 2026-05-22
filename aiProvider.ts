// Lazy load Google Generative AI on demand
let GoogleGenerativeAIClass: any = null;

export async function getGoogleAI() {
  if (!GoogleGenerativeAIClass) {
    // @ts-ignore
    GoogleGenerativeAIClass = (await import('@google/generative-ai')).GoogleGenerativeAI;
  }
  return GoogleGenerativeAIClass;
}

export async function initializeAI(apiKey: string) {
  const GoogleGenerativeAI = await getGoogleAI();
  return new GoogleGenerativeAI({ apiKey });
}
