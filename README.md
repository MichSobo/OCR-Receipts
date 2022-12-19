# OCR-Receipts
Application for receipt recognition 

## Process description

Flowchart for the main execution scheme.
```mermaid
flowchart TD
    A[Start main.py] --> B{{Args passed?}}
    B --yes--> C(Parse args)
    C --> D{{args correct?}}
    D --yes--> E{{config correct?}} 
    E --yes--> X[Run program]
    E --no--> Y[Return error]
    D --no--> Y
    B --no--> F{{config.json in workdir?}}
    F --yes--> E
    F --no--> G(Create default config)
    G --> Y
    
```

Flowchart for image processing.
```mermaid
flowchart TD
    A[Read image] --> B{{Adjust image?}}
    B --yes--> C(Resize) --> D(Adjust colors) --> E(Detect contours)
    E --> F(Apply perspective transformation)
    F --> G(OCR)
    G --> H{{Write content?}}
    H --yes--> I(Write content to file) --> J
    H --no --> J[Return content]
    B --no--> G
```