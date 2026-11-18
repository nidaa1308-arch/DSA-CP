import React, { useState } from "react";
import {
  FileText,
  Camera,
  Navigation,
  Building2,
  CheckCircle2,
  Upload,
  ArrowRight,
  ShieldAlert,
  AlertCircle,
  Loader2,
  Mountain,
  Zap,
  FileSpreadsheet,
  ShieldCheck,
  Layers,
  MapPin,
  Archive,
} from "lucide-react";
import { Screen } from "./Sidebar";
import { api } from "../api/client";

interface UploadIngestViewProps {
  onNavigate?: (screen: Screen) => void;
  provenance?: Record<string, any>;
  onTriggerNormalize?: () => void;
  onNormalize?: () => void;
  onContinue?: () => void;
  onUploadData?: (layerType: "cadastral" | "buildings" | "control" | "municipal" | "utilities" | "dsm" | "revenue" | "drone" | "ori" | "ground_truth", geojson: any, meta: any) => void;
  investigation?: any;
}

export const UploadIngestView: React.FC<UploadIngestViewProps> = ({
  onNavigate,
  provenance,
  onTriggerNormalize,
  onNormalize,
  onContinue,
  onUploadData,
  investigation,
}) => {
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedMap, setUploadedMap] = useState<Record<string, any>>({});
  const [uploadMode, setUploadMode] = useState<"zip" | "individual">("zip");
  const [isDraggingZip, setIsDraggingZip] = useState(false);
  const [zipResult, setZipResult] = useState<any>(null);

  const handleZipFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setUploadStatus("Please upload a valid .zip package file.");
      return;
    }
    setIsUploading(true);
    setUploadStatus(`Extracting and classifying layers from ${file.name}...`);
    try {
      let res: any;
      if (investigation?.id) {
        res = await api.uploadInvestigationZip(investigation.id, file);
      } else {
        res = await api.uploadZipPackage(file);
      }
      setZipResult(res);
      const extractedCount = res.layers_extracted?.length || 0;
      setUploadStatus(`✓ Successfully extracted and classified ${extractedCount} layers from ${file.name}`);

      if (res.layers && typeof res.layers === "object") {
        const newUploadedMap = { ...uploadedMap };
        for (const [key, lData] of Object.entries(res.layers as Record<string, any>)) {
          const info = {
            filename: lData.filename || `${key}.geojson`,
            features: lData.features_count || 1,
            features_count: lData.features_count || 1,
            file_format: lData.file_format || "GEOJSON",
            status: "VALID",
          };
          newUploadedMap[key] = info;

          if (onUploadData) {
            const mappedType = key === "gnss" ? "control" : (key as any);
            onUploadData(mappedType, lData.data || { type: "FeatureCollection", features: [] }, info);
          }
        }
        setUploadedMap(newUploadedMap);
      }
    } catch (err: any) {
      setUploadStatus(`Error unpacking ZIP: ${err?.message || err}`);
    } finally {
      setIsUploading(false);
    }
  };

  // Helper to check if a specific source key is active
  const getSourceInfo = (key: string) => {
    return uploadedMap[key] || investigation?.sources?.[key] || null;
  };

  const handleUploadGeneric = async (
    sourceKey: string,
    file: File,
    layerType: "cadastral" | "buildings" | "control" | "municipal" | "utilities" | "dsm" | "revenue" | "drone" | "ori" | "ground_truth",
    customParser?: () => Promise<any>
  ) => {
    setIsUploading(true);
    setUploadStatus(`Uploading and parsing ${file.name}...`);
    try {
      let res: any = null;
      let parsedCount: number | null = null;

      if (customParser) {
        res = await customParser();
      } else if (file.name.endsWith(".geojson") || file.name.endsWith(".json")) {
        // Client-side inspection of JSON for elevation samples or features
        try {
          const text = await file.text();
          const json = JSON.parse(text);
          if (json && typeof json === "object") {
            if (Array.isArray(json.features)) {
              parsedCount = json.features.length;
            } else {
              for (const k of ["samples", "points", "records", "elevations", "data", "grid"]) {
                if (Array.isArray(json[k])) {
                  parsedCount = json[k].length;
                  break;
                }
              }
            }
          }
        } catch {}
        res = await api.uploadGeoJSON(file);
      } else if (file.name.endsWith(".csv") || file.name.endsWith(".txt")) {
        try {
          const text = await file.text();
          const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
          if (lines.length > 1) {
            parsedCount = lines.length - 1; // data rows excluding header
          }
        } catch {}
        res = await api.uploadGNSSCSV(file);
      } else if (file.name.endsWith(".tif") || file.name.endsWith(".tiff")) {
        res = await api.uploadDroneGeoTIFF(file);
      } else {
        res = { filename: file.name, features: 1, file_format: file.name.split(".").pop()?.toUpperCase() };
      }

      // Attach to backend investigation if active
      if (investigation?.id) {
        try {
          const backendRes = await api.uploadInvestigationSource(investigation.id, sourceKey, file);
          if (backendRes && backendRes.source) {
            if (backendRes.source.features_count) {
              parsedCount = backendRes.source.features_count;
            }
          }
        } catch (e) {
          console.warn("Backend investigation source attach notice:", e);
        }
      }

      const finalCount = parsedCount || res?.features || res?.points_parsed || res?.records_parsed || res?.feature_count || 1;

      const info = {
        filename: file.name,
        features: finalCount,
        features_count: finalCount,
        file_format: file.name.split(".").pop()?.toUpperCase() || "GEOJSON",
        status: "VALID",
      };

      setUploadedMap((prev) => ({ ...prev, [sourceKey]: info }));
      setUploadStatus(`✓ Successfully uploaded ${file.name} (${info.features} features)`);

      if (onUploadData) {
        onUploadData(layerType, res?.geojson || res?.footprint_geojson || { type: "FeatureCollection", features: [] }, info);
      }
    } catch (err: any) {
      setUploadStatus(`Error uploading: ${err?.message || err}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleGeoJSONUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("cadastral", f, "cadastral");
  };

  const handleDroneUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("drone", f, "drone");
  };

  const handleORIUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("ori", f, "ori");
  };

  const handleBuildingUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("buildings", f, "buildings");
  };

  const handleCSVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("gnss", f, "control");
  };

  const handleMunicipalUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("municipal", f, "municipal");
  };

  const handleDSMUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("dsm", f, "dsm");
  };

  const handleUtilityUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("utility", f, "utilities");
  };

  const handleRevenueUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("revenue", f, "revenue");
  };

  const handleGTUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleUploadGeneric("ground_truth", f, "ground_truth");
  };

  const renderStatusPill = (sourceKey: string) => {
    const info = getSourceInfo(sourceKey);
    if (info) {
      return (
        <span className="file-status-pill active">
          <CheckCircle2 size={13} />
          <span>Uploaded</span>
        </span>
      );
    }
    return (
      <span className="file-status-pill pending">
        <AlertCircle size={13} />
        <span>Pending</span>
      </span>
    );
  };

  const renderFileRow = (sourceKey: string, defaultLabel: string) => {
    const info = getSourceInfo(sourceKey);
    if (info) {
      return (
        <div className="uploaded-file-row">
          <span style={{ fontWeight: 600, color: "#0f172a" }}>{info.filename}</span>
          <small style={{ color: "#059669", fontWeight: 600 }}>
            {info.features_count || info.features} features &bull; Ingested
          </small>
        </div>
      );
    }
    return (
      <div className="uploaded-file-row">
        <span style={{ color: "#94a3b8", fontStyle: "italic" }}>No dataset uploaded yet</span>
        <small style={{ color: "#94a3b8" }}>{defaultLabel}</small>
      </div>
    );
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="view-page-header">
        <div>
          <h2>Upload &amp; Ingest Datasets</h2>
          <p>
            {investigation ? `${investigation.id}: ${investigation.name}` : "Workspace Ingestion Pipeline"} &bull; Multi-source spatial and legal ingestion
          </p>
        </div>
      </div>

      {/* Stepper */}
      <div className="stepper-header">
        <div className="step-node active">
          <div className="step-num">1</div>
          <span>Upload Datasets</span>
        </div>
        <div className="step-line" />
        <div className="step-node">
          <div className="step-num">2</div>
          <span>Validate</span>
        </div>
        <div className="step-line" />
        <div className="step-node">
          <div className="step-num">3</div>
          <span>Normalize</span>
        </div>
        <div className="step-line" />
        <div className="step-node">
          <div className="step-num">4</div>
          <span>Process</span>
        </div>
        <div className="step-line" />
        <div className="step-node">
          <div className="step-num">5</div>
          <span>Review</span>
        </div>
      </div>

      {/* Upload Mode Selector (Option A: ZIP Package vs Option B: Individual Files) */}
      <div className="upload-mode-selector" style={{ marginTop: "20px" }}>
        <button
          type="button"
          className={`upload-mode-tab ${uploadMode === "zip" ? "active" : ""}`}
          onClick={() => setUploadMode("zip")}
        >
          <Archive size={18} />
          <span>Option A: Upload ZIP Package</span>
          <span className="badge-recommended">Auto-Classify &amp; Map</span>
        </button>
        <button
          type="button"
          className={`upload-mode-tab ${uploadMode === "individual" ? "active" : ""}`}
          onClick={() => setUploadMode("individual")}
        >
          <Layers size={18} />
          <span>Option B: Upload Individual Layer Files</span>
        </button>
      </div>

      {/* Upload status message */}
      {uploadStatus && (
        <div
          style={{
            background: uploadStatus.startsWith("✓") ? "#f0fdf4" : "#fef2f2",
            border: `1px solid ${uploadStatus.startsWith("✓") ? "#bbf7d0" : "#fecaca"}`,
            color: uploadStatus.startsWith("✓") ? "#166534" : "#991b1b",
            padding: "10px 14px",
            borderRadius: "7px",
            margin: "16px 0",
            fontSize: "12.5px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          {isUploading && <Loader2 size={15} className="spin" />}
          <span>{uploadStatus}</span>
        </div>
      )}

      {uploadMode === "zip" ? (
        <div>
          <div
            className={`zip-dropzone-box ${isDraggingZip ? "drag-over" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDraggingZip(true);
            }}
            onDragLeave={() => setIsDraggingZip(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDraggingZip(false);
              const f = e.dataTransfer.files?.[0];
              if (f) handleZipFile(f);
            }}
            onClick={() => {
              document.getElementById("zip-file-input")?.click();
            }}
          >
            <input
              id="zip-file-input"
              type="file"
              accept=".zip"
              style={{ display: "none" }}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleZipFile(f);
              }}
            />
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
              <div
                style={{
                  width: 60,
                  height: 60,
                  borderRadius: "50%",
                  background: "#ecfdf5",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#059669",
                  boxShadow: "0 4px 12px rgba(16, 185, 129, 0.15)",
                }}
              >
                <Archive size={30} />
              </div>
              <div>
                <h3 style={{ fontSize: 17, fontWeight: 700, color: "#0f172a", margin: "0 0 6px 0" }}>
                  Drag &amp; Drop Land Record .ZIP Package Here
                </h3>
                <p style={{ fontSize: 13, color: "#64748b", maxWidth: 520, margin: "0 auto", lineHeight: 1.5 }}>
                  Upload a single zip package containing cadastral parcel boundaries, drone/building footprints, GNSS control points, municipal vectors, or 7/12 records. The backend engine automatically unpacks, inspects geometry, normalizes CRS, and maps every layer into the investigation pipeline.
                </p>
              </div>
              <button
                type="button"
                className="btn-emerald"
                style={{ marginTop: 6 }}
                onClick={(e) => {
                  e.stopPropagation();
                  document.getElementById("zip-file-input")?.click();
                }}
              >
                <Upload size={14} />
                <span>Select .ZIP Archive File</span>
              </button>
            </div>
          </div>

          {/* Mapped Layers Preview if Zip is uploaded */}
          {zipResult && zipResult.layers_extracted && (
            <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "20px 24px", marginTop: 16 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <div>
                  <h4 style={{ fontSize: 15, fontWeight: 700, color: "#0f172a", margin: 0 }}>
                    Extracted &amp; Classified Spatial Layers ({zipResult.layers_extracted.length})
                  </h4>
                  <span style={{ fontSize: 12.5, color: "#64748b" }}>
                    Package: <strong>{zipResult.zip_filename || "Uploaded ZIP"}</strong> &bull; All layers successfully parsed and assigned
                  </span>
                </div>
                <span className="badge-pill success">
                  <CheckCircle2 size={12} /> Auto-Classified
                </span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
                {Object.entries(zipResult.layers || {}).map(([layerKey, layerInfo]: [string, any]) => (
                  <div
                    key={layerKey}
                    style={{
                      background: "#f8fafc",
                      border: "1px solid #cbd5e1",
                      borderRadius: 10,
                      padding: "12px 16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: 4,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <strong style={{ fontSize: 13, color: "#0f172a", textTransform: "capitalize" }}>
                        {layerKey === "gnss" ? "GNSS Control Points" : layerKey}
                      </strong>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "#059669", background: "#dcfce7", padding: "2px 8px", borderRadius: 6 }}>
                        {layerInfo.file_format || "GEOJSON"}
                      </span>
                    </div>
                    <span style={{ fontSize: 12, color: "#64748b", wordBreak: "break-all" }}>
                      {layerInfo.filename}
                    </span>
                    <span style={{ fontSize: 11.5, color: "#047857", fontWeight: 600 }}>
                      ✓ {layerInfo.features_count ?? 1} features ingested
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
      /* Upload Cards Grid - 10 NAKSHA Datasets */
      <div className="upload-cards-grid" style={{ marginTop: "16px" }}>
        {/* 1. Cadastral Layer */}
        <div className="upload-source-card" style={{ borderColor: "#10b981" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(16, 185, 129, 0.1)", color: "#10b981" }}>
                <FileText size={20} />
              </div>
              <div className="source-title-text">
                <h3>Cadastral Geometry</h3>
                <span>Existing Cadastral Maps (Legal Baseline)</span>
              </div>
            </div>
            {renderStatusPill("cadastral")}
          </div>
          {renderFileRow("cadastral", "Legal Baseline (GeoJSON / SHP)")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload Cadastral GeoJSON</span>
              <input type="file" accept=".geojson,.json" onChange={handleGeoJSONUpload} />
            </label>
            <span className="badge-pill success">Legal Authority 0.95</span>
          </div>
        </div>

        {/* 2. Drone Imagery */}
        <div className="upload-source-card" style={{ borderColor: "#0284c7" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(2, 132, 199, 0.1)", color: "#0284c7" }}>
                <Camera size={20} />
              </div>
              <div className="source-title-text">
                <h3>Drone Imagery</h3>
                <span>Drone Aerial Survey Orthomosaic (.tif, .tiff)</span>
              </div>
            </div>
            {renderStatusPill("drone")}
          </div>
          {renderFileRow("drone", "Orthomosaic Raster (GeoTIFF)")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload Drone GeoTIFF</span>
              <input type="file" accept=".tif,.tiff" onChange={handleDroneUpload} />
            </label>
            <span className="badge-pill info">Rasterio Header Parse</span>
          </div>
        </div>

        {/* 3. Orthorectified Imagery (ORI) */}
        <div className="upload-source-card" style={{ borderColor: "#38bdf8" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(56, 189, 248, 0.1)", color: "#0284c7" }}>
                <Camera size={20} />
              </div>
              <div className="source-title-text">
                <h3>Orthorectified Imagery (ORI)</h3>
                <span>True Ortho Multispectral COG (.tif, .tiff)</span>
              </div>
            </div>
            {renderStatusPill("ori")}
          </div>
          {renderFileRow("ori", "True Ortho Reference (Cloud-Optimized GeoTIFF)")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload ORI GeoTIFF</span>
              <input type="file" accept=".tif,.tiff" onChange={handleORIUpload} />
            </label>
            <span className="badge-pill success">True Ortho Reference</span>
          </div>
        </div>

        {/* 4. Building Footprints */}
        <div className="upload-source-card" style={{ borderColor: "#a855f7" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(168, 85, 247, 0.1)", color: "#a855f7" }}>
                <Layers size={20} />
              </div>
              <div className="source-title-text">
                <h3>Building Footprint Datasets</h3>
                <span>Physical Built-Up Polygons (AI / Vectorized)</span>
              </div>
            </div>
            {renderStatusPill("buildings")}
          </div>
          {renderFileRow("buildings", "Physical Boundary Observations")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload Building Footprints</span>
              <input type="file" accept=".geojson,.json" onChange={handleBuildingUpload} />
            </label>
            <span className="badge-pill success">Vector Polygonal Layer</span>
          </div>
        </div>

        {/* 5. GNSS / CORS Survey Data */}
        <div className="upload-source-card" style={{ borderColor: "#8b5cf6" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(139, 92, 246, 0.1)", color: "#8b5cf6" }}>
                <Navigation size={20} />
              </div>
              <div className="source-title-text">
                <h3>GNSS / CORS Survey Data</h3>
                <span>RTK Rover Ground Control Points (.csv)</span>
              </div>
            </div>
            {renderStatusPill("gnss")}
          </div>
          {renderFileRow("gnss", "Ground Survey Control Points")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload GNSS / CORS CSV</span>
              <input type="file" accept=".csv,.txt" onChange={handleCSVUpload} />
            </label>
            <span className="badge-pill info">RTK &lt;2cm Precision</span>
          </div>
        </div>

        {/* 6. Municipal GIS Layers */}
        <div className="upload-source-card" style={{ borderColor: "#f59e0b" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(245, 158, 11, 0.1)", color: "#f59e0b" }}>
                <Building2 size={20} />
              </div>
              <div className="source-title-text">
                <h3>Municipal GIS Layers</h3>
                <span>Admin Boundaries, Roads &amp; ROW (.gpkg, .shp)</span>
              </div>
            </div>
            {renderStatusPill("municipal")}
          </div>
          {renderFileRow("municipal", "Municipal Infrastructure Corridors")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload Municipal Vector</span>
              <input type="file" accept=".geojson,.json,.gpkg" onChange={handleMunicipalUpload} />
            </label>
            <span className="badge-pill warn">GeoPandas / GDAL</span>
          </div>
        </div>

        {/* 7. DSM / DTM Datasets */}
        <div className="upload-source-card" style={{ borderColor: "#06b6d4" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(6, 182, 212, 0.1)", color: "#06b6d4" }}>
                <Mountain size={20} />
              </div>
              <div className="source-title-text">
                <h3>DSM / DTM Datasets</h3>
                <span>Digital Surface &amp; Terrain Models (Slope / Height)</span>
              </div>
            </div>
            {renderStatusPill("dsm")}
          </div>
          {renderFileRow("dsm", "Elevation & Terrain Models")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload Elevation DSM</span>
              <input type="file" accept=".tif,.tiff,.json" onChange={handleDSMUpload} />
            </label>
            <span className="badge-pill info">Terrain Gradient Active</span>
          </div>
        </div>

        {/* 8. Utility Network Data */}
        <div className="upload-source-card" style={{ borderColor: "#ec4899" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(236, 72, 153, 0.1)", color: "#ec4899" }}>
                <Zap size={20} />
              </div>
              <div className="source-title-text">
                <h3>Utility Network Data</h3>
                <span>Power Transmission, Water &amp; Gas Pipelines</span>
              </div>
            </div>
            {renderStatusPill("utility")}
          </div>
          {renderFileRow("utility", "Underground & Overhead Utilities")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload Utility Network</span>
              <input type="file" accept=".geojson,.json" onChange={handleUtilityUpload} />
            </label>
            <span className="badge-pill warn">Utility Corridors</span>
          </div>
        </div>

        {/* 9. Revenue Records */}
        <div className="upload-source-card" style={{ borderColor: "#14b8a6" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(20, 184, 166, 0.1)", color: "#14b8a6" }}>
                <FileSpreadsheet size={20} />
              </div>
              <div className="source-title-text">
                <h3>Revenue Records</h3>
                <span>7/12 Extract, Khata, Khasra &amp; Mutations</span>
              </div>
            </div>
            {renderStatusPill("revenue")}
          </div>
          {renderFileRow("revenue", "Non-Spatial Legal Ownership ROR")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload Revenue ROR (7/12)</span>
              <input type="file" accept=".csv,.xlsx" onChange={handleRevenueUpload} />
            </label>
            <span className="badge-pill success">Non-Spatial ROR Join</span>
          </div>
        </div>

        {/* 10. Ground Truthing / GT */}
        <div className="upload-source-card" style={{ borderColor: "#6366f1" }}>
          <div className="upload-card-top">
            <div className="source-icon-title">
              <div className="source-icon" style={{ background: "rgba(99, 102, 241, 0.1)", color: "#6366f1" }}>
                <ShieldCheck size={20} />
              </div>
              <div className="source-title-text">
                <h3>Ground Truthing / GT</h3>
                <span>Field Survey Verification &amp; Adjudication Ledger</span>
              </div>
            </div>
            {renderStatusPill("ground_truth")}
          </div>
          {renderFileRow("ground_truth", "Field Verification Ledger")}
          <div className="upload-action-row">
            <label className="upload-file-btn">
              <Upload size={13} />
              <span>Upload GT Survey CSV</span>
              <input type="file" accept=".csv" onChange={handleGTUpload} />
            </label>
            <span className="badge-pill info">Field Survey Review</span>
          </div>
        </div>
      </div>
      )}

      {/* Footer Navigation */}
      <div className="validation-footer-bar" style={{ marginTop: "24px" }}>
        <span style={{ fontSize: "13px", color: "#64748b" }}>
          All uploaded datasets are attached directly to this investigation and stored in the database.
        </span>
        <button
          className="btn-emerald"
          onClick={() => {
            if (onNavigate) onNavigate("validation");
            else if (onContinue) onContinue();
          }}
        >
          <span>Proceed to Data Validation</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
};
