import { describe, expect, it } from "vitest";

import { sanitizeEmailText } from "./email-threading";

describe("email text sanitization without a browser DOM", () => {
  it("keeps safe text while removing executable markup before hydration", () => {
    const sanitizedText = sanitizeEmailText("<script>alert(1)</script>Safe");

    expect(sanitizedText).toBe("Safe");
  });
});
