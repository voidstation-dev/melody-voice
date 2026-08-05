// @vitest-environment jsdom

import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VieneuPage } from "./vieneu-page";

describe("VieneuPage", () => {
  it("renders both section labels and the unavailable state", () => {
    render(<VieneuPage />);

    expect(screen.getByRole("button", { name: /giọng nói/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /nhân bản giọng/i })).toBeInTheDocument();
    expect(screen.getByText(/đang tích hợp · chưa khả dụng/i)).toBeInTheDocument();
  });

  it("shows the preset-voices section by default", () => {
    render(<VieneuPage />);
    expect(screen.getByRole("heading", { name: /giọng nói \(preset\)/i })).toBeInTheDocument();
  });

  it("switches to the cloning section on click and shows its body copy", () => {
    render(<VieneuPage />);
    const cloningToggle = screen.getByRole("button", { name: /nhân bản giọng/i });
    fireEvent.click(cloningToggle);
    expect(
      screen.getByRole("heading", { name: /nhân bản giọng \(voice cloning\)/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/tạo giọng nói tùy chỉnh từ đoạn âm thanh tham chiếu/i),
    ).toBeInTheDocument();
    expect(cloningToggle).toHaveAttribute("aria-pressed", "true");
  });

  it("marks the active section toggle with aria-pressed", () => {
    render(<VieneuPage />);
    const voicesToggle = screen.getByRole("button", { name: /giọng nói/i });
    expect(voicesToggle).toHaveAttribute("aria-pressed", "true");
  });

  it("renders a disabled coming-soon action", () => {
    render(<VieneuPage />);
    const comingSoon = screen.getByRole("button", { name: /sắp ra mắt/i });
    expect(comingSoon).toBeDisabled();
  });
});