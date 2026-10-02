import type { InspectionResult, ProductConfig } from "@/types/inspection";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const defaultRequirements = [
  {
    id: "prod-detected",
    name: "Product detected",
    description: "The main product body should be clearly identified in the image.",
    required: true,
    severity: "critical" as const,
  },
  {
    id: "label-present",
    name: "Label present",
    description: "A label or branding region should be visible on the product front.",
    required: true,
    severity: "critical" as const,
  },
  {
    id: "cap-present",
    name: "Cap present",
    description: "The cap or closure should be visible and intact.",
    required: true,
    severity: "critical" as const,
  },
  {
    id: "logo-visible",
    name: "Logo visible",
    description: "Required logo or emblem should be visible in the expected region.",
    required: true,
    severity: "critical" as const,
  },
  {
    id: "no-packaging-damage",
    name: "Packaging damage",
    description: "The packaging should not show obvious damage or deformation.",
    required: true,
    severity: "warning" as const,
  },
];

export const defaultProduct: ProductConfig = {
  name: "Beverage Bottle",
  category: "Packaging",
  imageUrl: "",
  requirements: defaultRequirements,
};

export async function runInspection(product: ProductConfig): Promise<InspectionResult> {
  const response = await fetch(`${API_URL}/inspection`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: product.name,
      category: product.category,
      image_url: product.imageUrl || null,
      requirements: product.requirements,
    }),
  });

  if (!response.ok) {
    throw new Error("Inspection request failed. Please confirm the backend is running.");
  }

  return response.json() as Promise<InspectionResult>;
}
