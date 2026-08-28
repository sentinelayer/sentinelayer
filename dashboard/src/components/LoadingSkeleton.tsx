import React from "react";

export function LoadingSkeleton({ label = "Loading" }: { label?: string }): React.ReactElement {
  return (
    <div className="skeleton-card" role="status" aria-label={label}>
      <span className="skeleton skeleton-line" />
      <span className="skeleton skeleton-line" style={{ width: "72%", marginTop: "0.7rem" }} />
      <span className="skeleton skeleton-line" style={{ width: "48%", marginTop: "0.7rem" }} />
    </div>
  );
}
