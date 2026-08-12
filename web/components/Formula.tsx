import katex from "katex";
import "katex/dist/katex.min.css";

export function FormulaLatex({ tex }: { tex: string }) {
  const html = katex.renderToString(tex, {
    throwOnError: false,
    displayMode: true,
  });
  return (
    <div
      className="overflow-x-auto py-2 text-text"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export function FormulaInline({ tex }: { tex: string }) {
  const html = katex.renderToString(tex, { throwOnError: false });
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}