#!/usr/bin/env node

/**
 * Batch transform weekly gist files to strict template format.
 */

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { transformWeeklyBriefPublic, transformWeeklyGist, isStrictFormat } from "./lib/transform_strict.mjs";

/**
 * Main execution function.
 */
async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const write = args.includes("--write");
  const overwrite = args.includes("--overwrite");

  let dateFilter = null;
  const dateFlagIdx = args.findIndex((a) => a === "--date" || a.startsWith("--date="));
  if (dateFlagIdx >= 0) {
    const a = args[dateFlagIdx];
    dateFilter = a.startsWith("--date=") ? a.slice("--date=".length) : args[dateFlagIdx + 1];
  }

  if (!write && !dryRun) {
    console.log("Usage: node scripts/batch_transform.mjs [--dry-run] [--write] [--overwrite] [--date YYYY-MM-DD]");
    console.log("  --dry-run: Show what would be transformed without writing");
    console.log("  --write: Actually write the transformed files");
    console.log("  --overwrite: Overwrite existing _strict.md files");
    console.log("  --date: Only files whose basename contains this string (e.g. week end date)");
    process.exit(1);
  }

  const weeklyGistDir = "Weekly_Gist";
  const publicDir = path.join(weeklyGistDir, "Public");

  console.log("Batch transforming weekly gist files to strict template format...\n");

  // Find all files to transform
  const filesToTransform = [];

  // Find Weekly_Brief_Public files
  if (fs.existsSync(publicDir)) {
    const publicFiles = fs.readdirSync(publicDir)
      .filter(f => f.endsWith(".md") && f.startsWith("Weekly_Brief_Public_") && !f.endsWith("_strict.md"));
    
    for (const file of publicFiles) {
      filesToTransform.push({
        type: "brief",
        path: path.join(publicDir, file),
        outputPath: path.join(publicDir, file.replace(/\.md$/, "_strict.md"))
      });
    }
  }

  // Find Weekly_Gist files
  if (fs.existsSync(weeklyGistDir)) {
    const gistFiles = fs.readdirSync(weeklyGistDir)
      .filter(f => f.endsWith(".md") && f.startsWith("Weekly_Gist_") && !f.endsWith("_strict.md"));

    for (const file of gistFiles) {
      filesToTransform.push({
        type: "gist",
        path: path.join(weeklyGistDir, file),
        outputPath: path.join(weeklyGistDir, file.replace(/\.md$/, "_strict.md"))
      });
    }
  }

  let candidates = filesToTransform;
  if (dateFilter) {
    candidates = filesToTransform.filter((f) =>
      path.basename(f.path).includes(dateFilter)
    );
    console.log(`Date filter "${dateFilter}": ${candidates.length} of ${filesToTransform.length} files\n`);
  }

  console.log(`Found ${candidates.length} files to transform:\n`);

  let transformed = 0;
  let skipped = 0;
  let errors = 0;

  for (const fileInfo of candidates) {
    const { type, path: filePath, outputPath } = fileInfo;
    const filename = path.basename(filePath);

    try {
      // Check if output already exists
      if (fs.existsSync(outputPath) && !overwrite) {
        console.log(`⏭️  Skipping ${filename} (${type}): ${path.basename(outputPath)} already exists`);
        skipped++;
        continue;
      }

      // Read source file
      const content = fs.readFileSync(filePath, "utf-8");

      // Check if already in strict format
      if (isStrictFormat(content) && !overwrite) {
        console.log(`⏭️  Skipping ${filename} (${type}): Already appears to be in strict format`);
        skipped++;
        continue;
      }

      // Transform based on type
      let transformedContent;
      if (type === "brief") {
        transformedContent = transformWeeklyBriefPublic(content, filename);
      } else {
        transformedContent = transformWeeklyGist(content, filename);
      }

      if (dryRun) {
        console.log(`📝 Would transform ${filename} (${type}) → ${path.basename(outputPath)}`);
        console.log(`   Lines: ${content.split(/\r?\n/).length} → ${transformedContent.split(/\r?\n/).length}`);
        transformed++;
      } else if (write) {
        // Write transformed file
        fs.writeFileSync(outputPath, transformedContent, "utf-8");
        console.log(`✅ Transformed ${filename} (${type}) → ${path.basename(outputPath)}`);
        transformed++;
      }

    } catch (error) {
      console.error(`❌ Error transforming ${filename} (${type}):`, error.message);
      errors++;
    }
  }

  console.log("\n" + "=".repeat(50));
  console.log(`Summary:`);
  console.log(`  Transformed: ${transformed}`);
  console.log(`  Skipped: ${skipped}`);
  console.log(`  Errors: ${errors}`);
  console.log(`  Total: ${candidates.length}`);

  if (dryRun) {
    console.log("\nRun with --write to actually transform the files.");
  }

  process.exit(errors > 0 ? 1 : 0);
}

main().catch(error => {
  console.error("Fatal error:", error);
  process.exit(1);
});


