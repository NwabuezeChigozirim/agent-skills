"use strict";

const {
  AlignmentType,
  BorderStyle,
  HeadingLevel,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} = require("docx");

const PAGE_WIDTHS = {
  LETTER: 9360,
  A4: 9026,
};

function createHelpers(profile) {
  const brand = String(profile.brand_color || "1B5E3F").replace(/^#/, "").toUpperCase();
  const brandLight = String(profile.brand_light || "E8F1EC").replace(/^#/, "").toUpperCase();
  const dark = String(profile.text_color || "1F2933").replace(/^#/, "").toUpperCase();
  const grey = String(profile.muted_color || "6B7280").replace(/^#/, "").toUpperCase();
  const rule = String(profile.rule_color || "D6DEDA").replace(/^#/, "").toUpperCase();
  const font = String(profile.font || "Calibri");
  const contentWidth = PAGE_WIDTHS[profile.page_size] || PAGE_WIDTHS.LETTER;

  function heading(text, level) {
    const sizes = { 1: 30, 2: 25, 3: 22, 4: 20 };
    const headingLevels = {
      1: HeadingLevel.HEADING_1,
      2: HeadingLevel.HEADING_2,
      3: HeadingLevel.HEADING_3,
      4: HeadingLevel.HEADING_4,
    };
    return new Paragraph({
      heading: headingLevels[level] || HeadingLevel.HEADING_4,
      spacing: { before: level === 1 ? 360 : 240, after: 120 },
      border:
        level === 1
          ? { bottom: { style: BorderStyle.SINGLE, size: 6, color: rule, space: 6 } }
          : undefined,
      children: [
        new TextRun({
          text,
          bold: true,
          size: sizes[level] || 20,
          color: level === 1 || level === 3 ? brand : dark,
          font,
        }),
      ],
    });
  }

  function paragraph(children, options = {}) {
    const normalized = typeof children === "string" ? [run(children)] : children;
    return new Paragraph({
      spacing: {
        before: options.before || 0,
        after: options.after === undefined ? 120 : options.after,
      },
      alignment: options.alignment || AlignmentType.LEFT,
      numbering: options.numbering,
      children: normalized,
    });
  }

  function run(text, options = {}) {
    return new TextRun({
      text: String(text),
      bold: Boolean(options.bold),
      italics: Boolean(options.italics),
      font: options.code ? "Consolas" : font,
      size: options.size || (options.code ? 18 : 21),
      color: options.color || dark,
      break: options.break,
    });
  }

  function cellParagraph(children, options = {}) {
    const normalized = typeof children === "string" ? [run(children, options)] : children;
    return new Paragraph({
      spacing: { before: 35, after: 35 },
      alignment: options.alignment || AlignmentType.LEFT,
      children: normalized,
    });
  }

  function table(headers, rows) {
    const columnCount = Math.max(headers.length, ...rows.map((row) => row.length), 1);
    const base = Math.floor(contentWidth / columnCount);
    const widths = Array.from({ length: columnCount }, (_, index) =>
      index === columnCount - 1 ? contentWidth - base * (columnCount - 1) : base
    );
    const header = new TableRow({
      tableHeader: true,
      cantSplit: true,
      children: widths.map(
        (width, index) =>
          new TableCell({
            width: { size: width, type: WidthType.DXA },
            shading: { type: ShadingType.CLEAR, fill: brand, color: "auto" },
            margins: { top: 60, bottom: 60, left: 80, right: 80 },
            children: [cellParagraph(headers[index] || "", { bold: true, color: "FFFFFF" })],
          })
      ),
    });
    const body = rows.map(
      (row, rowIndex) =>
        new TableRow({
          cantSplit: true,
          children: widths.map(
            (width, columnIndex) =>
              new TableCell({
                width: { size: width, type: WidthType.DXA },
                shading: {
                  type: ShadingType.CLEAR,
                  fill: rowIndex % 2 ? "F5F8F6" : "FFFFFF",
                  color: "auto",
                },
                margins: { top: 60, bottom: 60, left: 80, right: 80 },
                children: [cellParagraph(row[columnIndex] || "")],
              })
          ),
        })
    );
    return new Table({
      columnWidths: widths,
      width: { size: contentWidth, type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.SINGLE, size: 2, color: rule },
        bottom: { style: BorderStyle.SINGLE, size: 2, color: rule },
        left: { style: BorderStyle.SINGLE, size: 2, color: rule },
        right: { style: BorderStyle.SINGLE, size: 2, color: rule },
        insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: rule },
        insideVertical: { style: BorderStyle.SINGLE, size: 2, color: rule },
      },
      rows: [header, ...body],
    });
  }

  function codeBlock(content, language = "") {
    const lines = String(content).replace(/\n$/, "").split("\n");
    const children = [];
    if (language) {
      children.push(paragraph([run(language, { bold: true, color: brand, size: 17 })], { after: 50 }));
    }
    for (const line of lines) {
      children.push(paragraph([run(line || " ", { code: true, size: 16 })], { after: 0 }));
    }
    return new Table({
      columnWidths: [contentWidth],
      width: { size: contentWidth, type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.SINGLE, size: 2, color: rule },
        bottom: { style: BorderStyle.SINGLE, size: 2, color: rule },
        left: { style: BorderStyle.SINGLE, size: 12, color: brand },
        right: { style: BorderStyle.SINGLE, size: 2, color: rule },
      },
      rows: [
        new TableRow({
          cantSplit: true,
          children: [
            new TableCell({
              width: { size: contentWidth, type: WidthType.DXA },
              shading: { type: ShadingType.CLEAR, fill: "F7F9F8", color: "auto" },
              margins: { top: 100, bottom: 100, left: 150, right: 120 },
              children,
            }),
          ],
        }),
      ],
    });
  }

  function callout(children) {
    return new Table({
      columnWidths: [contentWidth],
      width: { size: contentWidth, type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.SINGLE, size: 2, color: brand },
        bottom: { style: BorderStyle.SINGLE, size: 2, color: brand },
        left: { style: BorderStyle.SINGLE, size: 16, color: brand },
        right: { style: BorderStyle.SINGLE, size: 2, color: brand },
      },
      rows: [
        new TableRow({
          cantSplit: true,
          children: [
            new TableCell({
              width: { size: contentWidth, type: WidthType.DXA },
              shading: { type: ShadingType.CLEAR, fill: brandLight, color: "auto" },
              margins: { top: 100, bottom: 100, left: 150, right: 120 },
              children,
            }),
          ],
        }),
      ],
    });
  }

  function horizontalRule() {
    return new Paragraph({
      spacing: { before: 80, after: 120 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: rule, space: 4 } },
      children: [run("")],
    });
  }

  return {
    brand,
    dark,
    grey,
    font,
    contentWidth,
    heading,
    paragraph,
    run,
    table,
    codeBlock,
    callout,
    horizontalRule,
  };
}

module.exports = { createHelpers, PAGE_WIDTHS };
