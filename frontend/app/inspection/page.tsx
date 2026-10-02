"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { runInspection } from "@/lib/api";
import type { ProductConfig } from "@/types/inspection";

export default function InspectionPage() {
  const router = useRouter();
  const [product] = useState<ProductConfig | null>(() => {
    if (typeof window === "undefined") {
      return null;
    }

    const saved = window.localStorage.getItem("product-config");
    if (!saved) {
      return null;
    }

    return JSON.parse(saved) as ProductConfig;
  });
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!product && typeof window !== "undefined") {
      router.replace("/setup");
    }
  }, [product, router]);

  const handleRunInspection = async () => {
    if (!product) {
      return;
    }

    setIsRunning(true);
    setError("");

    try {
      const result = await runInspection(product);
      window.localStorage.setItem("inspection-result", JSON.stringify(result));
      router.push("/results");
    } catch (inspectionError) {
      setError(
        inspectionError instanceof Error
          ? inspectionError.message
          : "Inspection failed unexpectedly. Please try again.",
      );
    } finally {
      setIsRunning(false);
    }
  };

  if (!product) {
    return <div className="panel">Loading product configuration...</div>;
  }

  return (
    <div className="stacked-layout">
      <section className="panel hero-panel">
        <div>
          <p className="eyebrow">Inspection</p>
          <h1>{product.name}</h1>
          <p className="muted-text">
            Review the uploaded product image and launch a simulated inspection workflow against the configured rules.
          </p>
          <p className="muted-text">This is a mock validation flow for demo purposes and is not a live AI prediction system.</p>
        </div>
      </section>

      <section className="panel two-column-layout">
        <div className="inspection-image-panel">
          {product.imageUrl ? (
            <Image
              src={product.imageUrl}
              alt={product.name}
              className="inspection-image"
              width={1200}
              height={480}
              unoptimized
            />
          ) : (
            <div className="upload-placeholder large">No image selected</div>
          )}
        </div>

        <div className="inspection-summary">
          <div className="summary-chip">{product.category}</div>
          <h2>Requirements</h2>
          <ul className="inspection-checklist">
            {product.requirements.map((requirement) => (
              <li key={requirement.id}>
                <span className={`status-dot ${requirement.required ? "required" : "optional"}`} />
                {requirement.name}
              </li>
            ))}
          </ul>

          <div className="action-row">
            <Link href="/setup" className="secondary-button text-button">
              Edit setup
            </Link>
            <button type="button" className="primary-button" onClick={handleRunInspection} disabled={isRunning}>
              {isRunning ? "Running inspection..." : "Run inspection"}
            </button>
          </div>

          {error ? <p className="error-text">{error}</p> : null}
        </div>
      </section>
    </div>
  );
}
