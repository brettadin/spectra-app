### Example Sample JSON Schema

The javascript object notation (JSON) schema describing samples is minimal for flexibility and extensibility as it is produced by visual basic for applications (VBA) scripts in the [Non Targeted Analysis Method Reporting Tool (NTA-MRT)](dimspec-qc-home.html#dimspec-qc-ntamrt), and is not fully defined in a machine readability sense allowing for automatic schema verification.

This definition is intended only to facilitate transfer and assessment of data through the NTA-MRT into the DIMSpec schema, and sufficient for that purpose.

Any number of schema harmonization efforts could connect DIMSpec with larger schema development efforts within the community to increase machine readability and transferability in line with the FAIR principles. This is an area where the DIMSpec project can be improved and schema mapping efforts can serve to connect data with larger projects outside of this project. NIST welcomes collaborative efforts to harmonize schema with larger efforts; reach out with an [email to the PFAS program at NIST](/cdn-cgi/l/email-protection#a3d3c5c2d0e3cdcad0d78dc4ccd5) to start a collaboration.

```
{
  "sample": {
    "name",
    "description",
    "sample_class",
    "data_generator",
    "source"
  },
  "chromatography": {
    "ctype",
    "cvendor",
    "cmodel",
    "ssolvent",
    "mp1solvent",
    "mp1add",
    "m2solvent",
    "mp2add",
    "mp3solvent",
    "mp3add",
    "mp4solvent",
    "mp4add",
    "gcolvendor",
    "gcolname",
    "gcolchemistry",
    "gcolid",
    "gcollen",
    "gcoldp",
    "colvendor",
    "colname",
    "colchemistry",
    "colid",
    "collen",
    "coldp",
    "source"
  },
  "massspectrometry": {
    "msvendor",
    "msmodel",
    "ionization",
    "polarity",
    "voltage",
    "vunits",
    "massanalyzer1",
    "massanalyzer2",
    "fragmode",
    "ce_value",
    "ce_desc",
    "ce_units",
    "ms2exp",
    "isowidth",
    "msaccuracy",
    "ms1resolution",
    "ms2resolution",
    "source"
  },
  "qcmethod": [
    {
      "name",
      "value",
      "source":
    }
  ],
  "peaks": {
    "peak": {
      "count":,
      "name",
      "identifier",
      "ionstate",
      "mz",
      "rt",
      "peak_starttime",
      "peak_endtime",
      "confidence"
    }
  },
  "annotation": {
  "compound": {
      "name",
      "fragment": {
          "fragment_mz",
          "fragment_formula",
          "fragment_SMILES",
          "fragment_radical",
          "fragment_citation"
          }
      }
  }
}
```

### Example Peak JSON Schema Extension

The javascript object notation (JSON) schema describing peak data and quality control metrics is a minimal extension of the [sample schema](dimspec-qc-home.html#dimspec-qc-appendix-a) and is produced by the dimspec-qc tool and associated R functions used as part of the QC evaluation process. It is not fully defined in a machine readability sense allowing for automatic schema verification.

dimspec-qc uses this extension to split the provided sample schema by peak, maintaining the sample metadata, attach the âmsdataâ element containing anlytical results, and attach resulting QC data. This results in one file per peak for import into the DIMSpec schema, and is sufficient for that purpose.

Any number of future schema harmonization efforts could connect DIMSpec with larger schema development efforts within the community to increase machine reading and transferability in line with the FAIR principles. This is an area where the DIMSpec project can be improved and schema mapping efforts can serve to connect data with larger projects outside of this project. NIST welcomes collaborative efforts to harmonize schema with larger efforts; reach out with an [email to the PFAS program at NIST](/cdn-cgi/l/email-protection#b2c2d4d3c1f2dcdbc1c69cd5ddc4) to start a collaboration.

```
{
  ...,
  "msdata": [
    {
      "scantime",
      "ms_n",
      "baseion",
      "base_int",
      "measured_mz",
      "measured_intensity"
    }
  ],
  "qc": [
    [
      {
        "parameter",
        ...,
        "value",
        "limit",
        "result"
      }
    ]
  ]
}
```