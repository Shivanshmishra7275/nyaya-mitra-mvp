declare module '@google/generative-ai' {
  export class GoogleGenerativeAI {
    constructor(options: { apiKey: string });
    getGenerativeModel(options: { model: string; systemInstruction?: string }): GenerativeModel;
  }

  export interface GenerativeModel {
    generateContent(request: GenerateContentRequest): Promise<GenerateContentResponse>;
  }

  export interface GenerateContentRequest {
    contents: ContentRequest[];
    systemInstruction?: string;
  }

  export interface ContentRequest {
    role?: string;
    parts: Part[];
  }

  export interface Part {
    text?: string;
    inlineData?: { data: string; mimeType: string };
  }

  export interface GenerateContentResponse {
    response: {
      text(): string;
      candidates?: Array<{
        groundingMetadata?: {
          groundingChunks?: Array<{
            web?: { uri: string; title: string };
          }>;
        };
      }>;
    };
  }
}
