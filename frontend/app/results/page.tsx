"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import type { InspectionResult } from "@/types/inspection";

export default function ResultsPage() {
  const [result] = useState<InspectionResult | null>(() => {
    if (typeof window === "undefined") {
      return null;
    }

    const savedResult = window.localStorage.getItem("inspection-result");
    return savedResult ? (JSON.parse(savedResult) as InspectionResult) : null;
  });
  const [imageUrl] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }

    const savedConfig = window.localStorage.getItem("product-config");
    if (!savedConfig) {
      return "";
    }

    const parsedConfig = JSON.parse(savedConfig) as { imageUrl?: string };
    return parsedConfig.imageUrl || "";
  });

  if (!result) {
    return (
      <div className="panel">
        <p className="eyebrow">Results</p>
        <h1>No inspection result yet</h1>
        <p className="muted-text">Run an inspection from the setup flow to view the final report.</p>
        <div className="action-row">
          <Link href="/setup" className="primary-button">
            Start setup
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="stacked-layout">
      <section className="panel hero-panel results-topbar">
        <div>
          <p className="eyebrow">Inspection result</p>
          <h1>{result.product_name}</h1>
          <p className="muted-text">
            {result.inspection_mode === "yolo" ? "YOLO label detector" : "Mock simulation"} · Overall confidence:{" "}
            {Math.round(result.overall_confidence * 100)}%
          </p>
        </div>
        <div className={`result-badge ${result.passed ? "pass" : "fail"}`}>
          {result.passed ? "PASS" : "FAIL"}
        </div>
      </section>

      <section className="panel two-column-layout">
        <div className="inspection-image-panel">
          {imageUrl ? (
            <Image
              src={imageUrl}
              alt={result.product_name}
              className="inspection-image"
              width={1200}
              height={480}
              unoptimized
            />
          ) : (
            <div className="upload-placeholder large">No image available for this inspection</div>
          )}
        </div>

        <div className="inspection-summary">
          <h2>Summary</h2>
          <p>{result.summary}</p>
          <div className="meta-grid">
            <div>
              <span>Category</span>
              <strong>{result.category}</strong>
            </div>
            <div>
              <span>Generated</span>
              <strong>{new Date(result.generated_at).toLocaleString()}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="panel results-grid">
        <div>
          <h3>Checks</h3>
          <div className="results-list">
            {result.checks.map((check) => (
              <div key={check.id} className="check-card">
                <div className="check-header-row">
                  <strong>{check.name}</strong>
                  <span className={`pill ${check.passed ? "pass" : "fail"}`}>
                    {check.passed ? "Pass" : "Fail"}
                  </span>
                </div>
                <p>{check.explanation}</p>
                <small>Confidence: {Math.round(check.confidence * 100)}%</small>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3>Detections</h3>
          <div className="results-list">
            {result.detections.map((detection) => (
              <div key={detection.id} className="check-card">
                <div className="check-header-row">
                  <strong>{detection.label}</strong>
                  <span className="pill neutral">{detection.category}</span>
                </div>
                <p>Confidence: {Math.round(detection.confidence * 100)}%</p>
                {detection.bounding_box ? (
                  <small>
                    Box: {detection.bounding_box.map((coordinate) => coordinate.toFixed(3)).join(", ")}
                  </small>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="action-row">
        <Link href="/inspection" className="secondary-button text-button">
          Run again
        </Link>
        <Link href="/setup" className="primary-button">
          Edit requirements
        </Link>
      </div>
    </div>
  );
}
