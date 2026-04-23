import type { ContentBlock } from "../api/types";
import { ConsentGateView } from "./blocks/ConsentGateView";
import { CrisisBannerView } from "./blocks/CrisisBannerView";
import { ErrorBoundary } from "./ErrorBoundary";
import { FacilityBlockView } from "./blocks/FacilityBlockView";
import { FileSummaryView } from "./blocks/FileSummaryView";
import { PunnettBlockView } from "./blocks/PunnettBlockView";
import { ReferralView } from "./blocks/ReferralView";
import { StarterChipsView } from "./blocks/StarterChipsView";
import { TextBlockView } from "./blocks/TextBlockView";

function renderBlock(
  b: ContentBlock,
  i: number,
  onChipPick: (text: string) => void
) {
  switch (b.type) {
    case "text":
      return <TextBlockView key={i} block={b} />;
    case "starter_chips":
      return <StarterChipsView key={i} block={b} onPick={onChipPick} />;
    case "facility":
      return <FacilityBlockView key={i} block={b} />;
    case "punnett":
      return <PunnettBlockView key={i} block={b} />;
    case "crisis_banner":
      return <CrisisBannerView key={i} block={b} />;
    case "file_summary":
      return <FileSummaryView key={i} block={b} />;
    case "referral":
      return <ReferralView key={i} block={b} />;
    case "consent_gate":
      return <ConsentGateView key={i} block={b} />;
    default:
      return null;
  }
}

export function MessageContent({
  blocks,
  onChipPick,
}: {
  blocks: ContentBlock[];
  onChipPick: (text: string) => void;
}) {
  return (
    <>
      {blocks.map((b, i) => (
        <ErrorBoundary
          key={i}
          fallback={() => (
            <div className="text-xs text-rose-700 italic">
              (content block failed to render)
            </div>
          )}
        >
          {renderBlock(b, i, onChipPick)}
        </ErrorBoundary>
      ))}
    </>
  );
}
