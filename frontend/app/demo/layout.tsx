/**
 * The demo replay stays dark.
 *
 * The showcase is a clean white advertisement; the replay is the agent's own
 * face, and it shares a palette with `/dj` and the engineering view on purpose
 * — footage reads better on dark, and the two should look like one product.
 *
 * `data-theme="dark"` re-points the tokens in globals.css for this subtree
 * only. Nothing here hardcodes a colour.
 */
export default function DemoLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div data-theme="dark" className="h-dvh overflow-hidden bg-plane text-ink-primary">
      {children}
    </div>
  );
}
