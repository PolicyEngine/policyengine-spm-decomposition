import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useDecompositionData } from "../hooks/useDecompositionData";
import { TEST_DATA } from "./testData";

describe("useDecompositionData", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("starts in loading state", () => {
    globalThis.fetch = vi.fn(
      () => new Promise(() => {}), // never resolves
    ) as unknown as typeof fetch;

    const { result } = renderHook(() => useDecompositionData());

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("fetches and returns decomposition data", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(TEST_DATA),
      }),
    ) as unknown as typeof fetch;

    const { result } = renderHook(() => useDecompositionData());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(TEST_DATA);
    expect(result.current.error).toBeNull();
    expect(globalThis.fetch).toHaveBeenCalledWith("/decomposition.json");
  });

  it("handles fetch error", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 404,
      }),
    ) as unknown as typeof fetch;

    const { result } = renderHook(() => useDecompositionData());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("HTTP 404");
  });

  it("handles network error", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.reject(new Error("Network failure")),
    ) as unknown as typeof fetch;

    const { result } = renderHook(() => useDecompositionData());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("Network failure");
  });
});
