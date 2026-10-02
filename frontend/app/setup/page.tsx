"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChangeEvent, useState } from "react";

import { defaultProduct } from "@/lib/api";
import type { ProductConfig, Requirement } from "@/types/inspection";

const categoryOptions = [
  "Packaging",
  "Electronics",
  "Food & Beverage",
  "Pharmaceutical",
  "Industrial",
  "Consumer Goods",
];

const buildDefaultRequirements = (): Requirement[] =>
  defaultProduct.requirements.map((item) => ({ ...item }));

export default function SetupPage() {
  const router = useRouter();
  const [product, setProduct] = useState<ProductConfig>(() => {
    if (typeof window === "undefined") {
      return defaultProduct;
    }

    const saved = window.localStorage.getItem("product-config");
    return saved ? (JSON.parse(saved) as ProductConfig) : defaultProduct;
  });
  const [imagePreview, setImagePreview] = useState<string>(() => {
    if (typeof window === "undefined") {
      return defaultProduct.imageUrl;
    }

    const saved = window.localStorage.getItem("product-config");
    if (!saved) {
      return defaultProduct.imageUrl;
    }

    const parsed = JSON.parse(saved) as ProductConfig;
    return parsed.imageUrl || "";
  });

  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const preview = typeof reader.result === "string" ? reader.result : "";
      setImagePreview(preview);
      setProduct((current) => ({ ...current, imageUrl: preview }));
    };
    reader.readAsDataURL(file);
  };

  const handleRequirementToggle = (id: string) => {
    setProduct((current) => ({
      ...current,
      requirements: current.requirements.map((item) =>
        item.id === id ? { ...item, required: !item.required } : item,
      ),
    }));
  };

  const handleSave = () => {
    window.localStorage.setItem("product-config", JSON.stringify(product));
    router.push("/inspection");
  };

  return (
    <div className="stacked-layout">
      <section className="panel hero-panel">
        <div>
          <p className="eyebrow">Product setup</p>
          <h1>Define the product and the rules to check</h1>
          <p className="muted-text">
            Configure the product, upload the reference image, and set a clear inspection checklist.
          </p>
        </div>
      </section>

      <section className="panel form-panel">
        <div className="field-grid">
          <label className="field">
            <span>Product name</span>
            <input
              value={product.name}
              onChange={(event) => setProduct({ ...product, name: event.target.value })}
              placeholder="e.g. Beverage Bottle"
            />
          </label>

          <label className="field">
            <span>Product category</span>
            <select
              value={product.category}
              onChange={(event) => setProduct({ ...product, category: event.target.value })}
            >
              {categoryOptions.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="field upload-field">
          <span>Reference image</span>
          <input type="file" accept="image/*" onChange={handleImageUpload} />
          {imagePreview ? (
            <Image
              src={imagePreview}
              alt="Selected product preview"
              className="upload-preview"
              width={1200}
              height={480}
              unoptimized
            />
          ) : (
            <div className="upload-placeholder">Upload a product image to begin inspection</div>
          )}
        </label>

        <div className="requirement-box">
          <div className="section-header-row">
            <h3>Inspection requirements</h3>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setProduct((current) => ({ ...current, requirements: buildDefaultRequirements() }))}
            >
              Reset defaults
            </button>
          </div>

          <div className="requirement-list">
            {product.requirements.map((requirement) => (
              <div key={requirement.id} className="requirement-item">
                <label className="toggle-row">
                  <input
                    type="checkbox"
                    checked={requirement.required}
                    onChange={() => handleRequirementToggle(requirement.id)}
                  />
                  <div>
                    <strong>{requirement.name}</strong>
                    <p>{requirement.description}</p>
                  </div>
                </label>
              </div>
            ))}
          </div>
        </div>

        <div className="action-row">
          <Link href="/" className="secondary-button text-button">
            Back to dashboard
          </Link>
          <button type="button" className="primary-button" onClick={handleSave}>
            Start inspection
          </button>
        </div>
      </section>
    </div>
  );
}
