import type { TextBlock } from "../../api/types";

export function TextBlockView({ block }: { block: TextBlock }) {
  const paragraphs = block.text.split(/\n{2,}/).map((s) => s.trim()).filter(Boolean);
  return (
    <div className="prose prose-stone dark:prose-invert max-w-none prose-p:my-2 prose-li:my-0.5">
      {paragraphs.map((p, i) => (
        <p key={i} className="text-[15.5px] leading-7 text-ink dark:text-slate-100 whitespace-pre-wrap">
          {p}
        </p>
      ))}
    </div>
  );
}
