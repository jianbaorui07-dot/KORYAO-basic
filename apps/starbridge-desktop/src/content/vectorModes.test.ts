import { describe, expect, it } from "vitest";

import { VECTOR_MODES } from "./vectorModes";

describe("editable-99 mode", () => {
  it("presents the verified quality mode without relabeling another preset", () => {
    expect(VECTOR_MODES.find((mode) => mode.id === "editable-99")).toEqual({
      id: "editable-99",
      name: "99% 可编辑",
      description: "逐候选回渲染，全部质量门槛通过后再选择复杂度更低的 SVG。",
      bestFor: "高保真且需继续编辑的交付",
    });
  });
});
