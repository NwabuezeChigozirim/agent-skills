"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");

const renderer = path.resolve(__dirname, "..", "scripts", "render_docx.js");

function fixture(documentType = "FSD", body = "## Scope\n\nBehavioral text.\n") {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "spec-chain-render-test-"));
  const docs = path.join(root, "docs");
  const exportsDirectory = path.join(docs, "exports");
  fs.mkdirSync(exportsDirectory, { recursive: true });
  const input = path.join(docs, `sample-${documentType}.md`);
  fs.writeFileSync(
    input,
    `---\ndocument_type: ${documentType}\nproject: sample\n---\n# Sample ${documentType}\n\n${body}`,
    "utf8"
  );
  return { root, docs, exportsDirectory, input };
}

function render(args, cwd) {
  return spawnSync(process.execPath, [renderer, ...args], {
    cwd,
    encoding: "utf8",
    timeout: 30000,
  });
}

test("renders canonical Markdown to a derived DOCX", (t) => {
  const item = fixture();
  t.after(() => fs.rmSync(item.root, { recursive: true, force: true }));
  const output = path.join(item.exportsDirectory, "sample.docx");
  const result = render(
    ["--input", item.input, "--profile", "internal", "--output", output],
    item.root
  );
  assert.equal(result.status, 0, result.stderr);
  assert.ok(fs.statSync(output).size > 1000);
  assert.equal(fs.readFileSync(output, { encoding: null, flag: "r" }).subarray(0, 2).toString(), "PK");
});

test("single verify flag creates PDF and page images", (t) => {
  const item = fixture();
  t.after(() => fs.rmSync(item.root, { recursive: true, force: true }));
  const output = path.join(item.exportsDirectory, "verified.docx");
  const result = render(
    ["--input", item.input, "--profile", "internal", "--output", output, "--verify"],
    item.root
  );
  assert.equal(result.status, 0, result.stderr);
  assert.ok(fs.existsSync(path.join(item.exportsDirectory, "verified.pdf")));
  const pages = fs.readdirSync(path.join(item.exportsDirectory, "verified-pages"));
  assert.ok(pages.some((name) => name.endsWith(".png")));
});

test("rejects output outside the derived exports directory", (t) => {
  const item = fixture();
  t.after(() => fs.rmSync(item.root, { recursive: true, force: true }));
  const result = render(
    ["--input", item.input, "--profile", "internal", "--output", path.join(item.docs, "wrong.docx")],
    item.root
  );
  assert.equal(result.status, 2);
  assert.match(result.stderr, /must be written under/);
});

test("client profile rejects technical design exports", (t) => {
  const item = fixture("TSD", "## Architecture\n\nTechnical detail.\n");
  t.after(() => fs.rmSync(item.root, { recursive: true, force: true }));
  const output = path.join(item.exportsDirectory, "client.docx");
  const result = render(
    ["--input", item.input, "--profile", "client", "--output", output],
    item.root
  );
  assert.equal(result.status, 2);
  assert.match(result.stderr, /TSD cannot be exported/);
});
