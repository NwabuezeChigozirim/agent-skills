#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const MarkdownIt = require("markdown-it");
const {
  AlignmentType,
  Document,
  Footer,
  LevelFormat,
  PageBreak,
  PageNumber,
  Packer,
  Paragraph,
  TextRun,
} = require("docx");
const { createHelpers } = require("./docx_helpers");

const PAGE = {
  LETTER: { width: 12240, height: 15840 },
  A4: { width: 11906, height: 16838 },
};

function fail(message) {
  process.stderr.write(`error: ${message}\n`);
  process.exit(2);
}

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith("--")) fail(`unexpected argument: ${key}`);
    if (key === "--verify") {
      result.verify = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) fail(`missing value for ${key}`);
    result[key.slice(2)] = value;
    index += 1;
  }
  for (const required of ["input", "profile", "output"]) {
    if (!result[required]) fail(`--${required} is required`);
  }
  return result;
}

function verifyRender(output) {
  const outputDirectory = path.dirname(output);
  const stem = path.basename(output, path.extname(output));
  const pdf = path.join(outputDirectory, `${stem}.pdf`);
  const pages = path.join(outputDirectory, `${stem}-pages`);
  const libreOfficeHome = fs.mkdtempSync(path.join(os.tmpdir(), "spec-chain-libreoffice-"));
  try {
    const converted = spawnSync(
      "soffice",
      [
        `-env:UserInstallation=file://${libreOfficeHome}`,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        outputDirectory,
        output,
      ],
      { encoding: "utf8" }
    );
    if (converted.status !== 0 || !fs.existsSync(pdf)) {
      fail(`DOCX-to-PDF verification failed: ${converted.stderr || converted.stdout}`);
    }
    fs.mkdirSync(pages, { recursive: true });
    const rendered = spawnSync(
      "pdftoppm",
      ["-png", "-r", "90", pdf, path.join(pages, "page")],
      { encoding: "utf8" }
    );
    if (rendered.status !== 0) {
      fail(`PDF page rendering failed: ${rendered.stderr || rendered.stdout}`);
    }
    const pageFiles = fs.readdirSync(pages).filter((name) => name.endsWith(".png")).sort();
    if (!pageFiles.length) fail("PDF page rendering produced no images");
    return { pdf, pages: pageFiles.map((name) => path.join(pages, name)) };
  } finally {
    fs.rmSync(libreOfficeHome, { recursive: true, force: true });
  }
}

function parseFrontmatter(source) {
  if (!source.startsWith("---\n")) return { attributes: {}, body: source };
  const end = source.indexOf("\n---\n", 4);
  if (end < 0) fail("unterminated YAML frontmatter");
  const attributes = {};
  for (const line of source.slice(4, end).split("\n")) {
    const split = line.indexOf(":");
    if (split < 0) continue;
    attributes[line.slice(0, split).trim()] = line.slice(split + 1).trim();
  }
  return { attributes, body: source.slice(end + 5) };
}

function loadProfile(value, skillRoot) {
  const named = path.resolve(skillRoot, "assets", "profiles", `${value}.json`);
  const candidate = fs.existsSync(named) ? named : path.resolve(value);
  if (!fs.existsSync(candidate)) fail(`profile not found: ${value}`);
  const profile = JSON.parse(fs.readFileSync(candidate, "utf8"));
  if (!["internal", "client"].includes(profile.name)) {
    fail("profile name must be internal or client");
  }
  if (!PAGE[profile.page_size]) fail(`unsupported page size: ${profile.page_size}`);
  return profile;
}

function assertDerivedOutput(input, output) {
  const exportsRoot = path.resolve(path.dirname(input), "exports");
  const relative = path.relative(exportsRoot, output);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    fail(`derived DOCX must be written under ${exportsRoot}`);
  }
}

function assertClientSafe(body, attributes) {
  if (String(attributes.document_type || "").toUpperCase() === "TSD") {
    fail("TSD cannot be exported as a client behavioral edition");
  }
  const forbidden = [
    /^#{1,6}\s+(architecture|technology|repository|data design|deployment|implementation)\b/im,
    /\b(database schema|source path|deployment topology|node_modules|kubernetes|dockerfile)\b/i,
  ];
  for (const pattern of forbidden) {
    if (pattern.test(body)) fail(`client profile rejected implementation detail matching ${pattern}`);
  }
}

function inlineRuns(token, helpers) {
  const children = token.children || [];
  const runs = [];
  const style = { bold: false, italics: false, code: false, link: false };
  for (const child of children) {
    if (child.type === "strong_open") style.bold = true;
    else if (child.type === "strong_close") style.bold = false;
    else if (child.type === "em_open") style.italics = true;
    else if (child.type === "em_close") style.italics = false;
    else if (child.type === "link_open") style.link = true;
    else if (child.type === "link_close") style.link = false;
    else if (child.type === "code_inline") {
      runs.push(helpers.run(child.content, { code: true }));
    } else if (child.type === "softbreak" || child.type === "hardbreak") {
      runs.push(helpers.run("", { break: 1 }));
    } else if (child.type === "image") {
      runs.push(helpers.run(`[image: ${child.content || "untitled"}]`, { italics: true }));
    } else if (child.type === "text") {
      runs.push(
        helpers.run(child.content, {
          bold: style.bold,
          italics: style.italics,
          color: style.link ? helpers.brand : helpers.dark,
        })
      );
    } else if (child.content) {
      runs.push(helpers.run(child.content));
    }
  }
  return runs.length ? runs : [helpers.run(token.content || "")];
}

function inlinePlain(token) {
  const children = token.children || [];
  const parts = [];
  for (const child of children) {
    if (child.type === "text" || child.type === "code_inline") parts.push(child.content);
    else if (child.type === "softbreak" || child.type === "hardbreak") parts.push(" ");
    else if (child.type === "image") parts.push(`[image: ${child.content || "untitled"}]`);
  }
  return parts.join("") || token.content;
}

function collectTable(tokens, start) {
  let index = start + 1;
  let header = [];
  const rows = [];
  let current = [];
  let inHead = false;
  while (index < tokens.length && tokens[index].type !== "table_close") {
    const token = tokens[index];
    if (token.type === "thead_open") inHead = true;
    else if (token.type === "thead_close") inHead = false;
    else if (token.type === "tr_open") current = [];
    else if (token.type === "inline") current.push(inlinePlain(token));
    else if (token.type === "tr_close") {
      if (inHead && !header.length) header = current;
      else rows.push(current);
    }
    index += 1;
  }
  return { header, rows, end: index };
}

function markdownBlocks(body, helpers) {
  const md = new MarkdownIt({ html: false, linkify: true, typographer: true });
  const tokens = md.parse(body, {});
  const blocks = [];
  const headings = [];
  const listStack = [];
  let orderedInstance = 0;
  let inListItem = false;
  let quoteChildren = null;
  let firstH1Skipped = false;

  const emit = (block) => {
    if (quoteChildren) quoteChildren.push(block);
    else blocks.push(block);
  };

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.type === "heading_open") {
      const level = Number(token.tag.slice(1));
      const inline = tokens[index + 1];
      const title = inline.content;
      if (level === 1 && !firstH1Skipped) {
        firstH1Skipped = true;
      } else {
        headings.push({ level, title });
        emit(helpers.heading(title, level));
      }
      index += 2;
    } else if (token.type === "paragraph_open") {
      const inline = tokens[index + 1];
      const currentList = listStack[listStack.length - 1];
      const numbering =
        inListItem && currentList
          ? {
              reference: currentList.type === "ordered" ? "numbers" : "bullets",
              level: Math.min(listStack.length - 1, 2),
              instance: currentList.instance,
            }
          : undefined;
      emit(helpers.paragraph(inlineRuns(inline, helpers), { numbering }));
      index += 2;
    } else if (token.type === "bullet_list_open") {
      listStack.push({ type: "bullet", instance: 0 });
    } else if (token.type === "ordered_list_open") {
      orderedInstance += 1;
      listStack.push({ type: "ordered", instance: orderedInstance });
    } else if (token.type === "bullet_list_close" || token.type === "ordered_list_close") {
      listStack.pop();
    } else if (token.type === "list_item_open") {
      inListItem = true;
    } else if (token.type === "list_item_close") {
      inListItem = false;
    } else if (token.type === "fence" || token.type === "code_block") {
      emit(helpers.codeBlock(token.content, token.info.trim()));
    } else if (token.type === "table_open") {
      const parsed = collectTable(tokens, index);
      emit(helpers.table(parsed.header, parsed.rows));
      index = parsed.end;
    } else if (token.type === "blockquote_open") {
      quoteChildren = [];
    } else if (token.type === "blockquote_close") {
      const content = quoteChildren;
      quoteChildren = null;
      blocks.push(helpers.callout(content.length ? content : [helpers.paragraph("")]));
    } else if (token.type === "hr") {
      emit(helpers.horizontalRule());
    }
  }
  return { blocks, headings };
}

function cover(attributes, title, profile, helpers, input) {
  const lines = [
    helpers.paragraph([helpers.run(attributes.project || "Project", { bold: true, size: 38, color: helpers.brand })], {
      alignment: AlignmentType.CENTER,
      before: 2500,
      after: 180,
    }),
    helpers.paragraph([helpers.run(title, { bold: true, size: 34 })], {
      alignment: AlignmentType.CENTER,
      after: 180,
    }),
    helpers.paragraph([helpers.run(profile.title_suffix || "", { size: 23, color: helpers.grey })], {
      alignment: AlignmentType.CENTER,
      after: 400,
    }),
    helpers.paragraph(
      [helpers.run(`Derived from canonical Markdown: ${path.basename(input)}`, { italics: true, color: helpers.grey })],
      { alignment: AlignmentType.CENTER, after: 100 }
    ),
  ];
  if (profile.confidentiality) {
    lines.push(
      helpers.paragraph([helpers.run(profile.confidentiality, { italics: true, color: helpers.brand })], {
        alignment: AlignmentType.CENTER,
        after: 100,
      })
    );
  }
  return lines;
}

function contents(headings, helpers) {
  const result = [helpers.heading("Contents", 1)];
  for (const heading of headings.filter((item) => item.level <= 3)) {
    result.push(
      helpers.paragraph([helpers.run(heading.title, { bold: heading.level === 1 })], {
        before: heading.level === 1 ? 100 : 0,
        after: 25,
      })
    );
  }
  result.push(new Paragraph({ children: [new PageBreak()] }));
  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const input = path.resolve(args.input);
  const output = path.resolve(args.output);
  if (!fs.existsSync(input)) fail(`input not found: ${input}`);
  assertDerivedOutput(input, output);
  const profile = loadProfile(args.profile, path.resolve(__dirname, ".."));
  const source = fs.readFileSync(input, "utf8");
  const { attributes, body } = parseFrontmatter(source);
  if (profile.name === "client") assertClientSafe(body, attributes);

  const helpers = createHelpers(profile);
  const { blocks, headings } = markdownBlocks(body, helpers);
  const title = headings.find((item) => item.level === 1)?.title || path.basename(input, ".md");
  const page = PAGE[profile.page_size];
  const footer = new Footer({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({
            text: `${attributes.document_type || "SPEC"} · Derived export · Page `,
            size: 16,
            color: helpers.grey,
            font: helpers.font,
          }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, color: helpers.grey, font: helpers.font }),
        ],
      }),
    ],
  });
  const numbering = {
    config: [
      {
        reference: "bullets",
        levels: [0, 1, 2].map((level) => ({
          level,
          format: LevelFormat.BULLET,
          text: level === 0 ? "•" : level === 1 ? "◦" : "▪",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 360 + level * 300, hanging: 220 } } },
        })),
      },
      {
        reference: "numbers",
        levels: [0, 1, 2].map((level) => ({
          level,
          format: LevelFormat.DECIMAL,
          text: level === 0 ? "%1." : level === 1 ? "%2." : "%3.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400 + level * 300, hanging: 260 } } },
        })),
      },
    ],
  };
  const document = new Document({
    numbering,
    styles: { default: { document: { run: { font: helpers.font, size: 21, color: helpers.dark } } } },
    sections: [
      {
        properties: { page: { size: page, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
        children: cover(attributes, title, profile, helpers, input),
      },
      {
        properties: { page: { size: page, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
        footers: { default: footer },
        children: [...contents(headings, helpers), ...blocks],
      },
    ],
  });
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const buffer = await Packer.toBuffer(document);
  fs.writeFileSync(output, buffer, { mode: 0o644 });
  process.stdout.write(`${output}\n`);
  if (args.verify) {
    const verified = verifyRender(output);
    process.stdout.write(`${verified.pdf}\n`);
    for (const page of verified.pages) process.stdout.write(`${page}\n`);
  }
}

main().catch((error) => fail(error.stack || error.message));
