# PACE/PANCE Campaign Builder

A Streamlit application for building and visualizing PACE (Phage-Assisted Continuous Evolution) and PANCE (Phage-Assisted Non-Continuous Evolution) campaigns.

## Features

### Campaign Management
- **Campaign Configuration**: Set up campaign metadata, starting proteins, and host systems
- **Selection Circuits**: Define promoter systems and selection mechanisms
- **Experimental Arms**: Create multiple experimental pathways
- **Segments**: Define PACE/PANCE phases with time progression
- **Lagoons & Samples**: Track experimental conditions and sample collection
- **Analyses**: Record analysis pipelines and results
- **Attachments**: Store related files (SOPs, plasmid maps, figures)

### Real-time Visualization
- **Interactive Schematic**: Visualize your campaign structure as you build it
- **Time-based Progression**: See promoter evolution over time
- **Pathway Comparison**: Compare T3 and SP6 pathways side-by-side
- **Color-coded Promoters**: Easy identification of different promoter types
- **Sample Data**: Load demonstration data to see the visualization in action

## Getting Started

### Prerequisites
```bash
pip install streamlit plotly jsonschema pyyaml python-dateutil
```

### Running the App
```bash
streamlit run pacemaker.py
```

### Using the Visualization

1. **Start with Sample Data**: Click "📊 Load Sample Data" in the Schematic tab to see a demonstration
2. **Build Your Campaign**: 
   - Create experimental arms in "Arms & Timepoints"
   - Define selection circuits in "Selection Circuits" 
   - Add segments with time progression in "Segments"
3. **View Real-time Updates**: The schematic automatically updates as you add data

## Visualization Features

### Color Legend
- **🔴 T7/T3**: Initial T3 pathway (light red/pink)
- **🟠 T3**: T3 promoter phase (orange)
- **🟢 T3/final**: T3 to final transition (olive green)
- **🔵 T7/SP6**: Initial SP6 pathway (light blue)
- **🟢 SP6**: SP6 promoter phase (green)
- **🔷 SP6/final**: SP6 to final transition (teal)
- **🟢 Final**: Final promoter (green)

### Visual Elements
- **Horizontal rows**: Experimental arms
- **Colored rectangles**: Time periods for each segment
- **Arrows (→)**: Progression between segments
- **Background shading**: Pathway grouping (T3 vs SP6)
- **Time markers**: 24-hour intervals on x-axis
- **Labels**: Segment ID, mode, and stepping stones

## Data Export

The app supports exporting your campaign data in:
- **JSON format**: For programmatic access
- **YAML format**: For human-readable configuration

## Schema Validation

All campaign data is validated against a comprehensive JSON schema that ensures:
- Required fields are present
- Data types are correct
- Time relationships are logical
- Selection circuit configurations are valid

## Example Campaign Structure

The sample data demonstrates a typical PACE campaign with:
- Two experimental arms (T3 and SP6 pathways)
- Three segments per arm showing promoter progression
- Time-based evolution from initial to final promoters
- Proper selection circuit definitions

## Contributing

This is a work in progress. The app is designed to be extensible for additional visualization types and data formats.

## License

This project is for research and educational use.
