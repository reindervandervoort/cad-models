#!/usr/bin/env python3
"""
Simple Demo Model - Creates a basic cube
Based on the bolt_pattern example structure
"""

import FreeCAD
import Part


def generate_model():
    """
    Generate a simple cube model that exports correctly to STL.
    This follows the pattern used in the backend examples.
    """
    print("Starting demo model generation...")

    # Create new document
    doc = FreeCAD.newDocument("Demo")
    print("✓ Document created")

    # Create a cube (100x100x100 mm)
    cube_shape = Part.makeBox(100, 100, 100)
    print("✓ Cube shape created")

    # Add cube to document as a Part::Feature
    cube_obj = doc.addObject("Part::Feature", "DemoCube")
    cube_obj.Shape = cube_shape
    print("✓ Cube object added to document")

    # Recompute to ensure everything is updated
    doc.recompute()
    print("✓ Document recomputed")

    print(f"✓ Demo model generated successfully with {len(doc.Objects)} object(s)")

    # Return the document for STL export
    return doc


if __name__ == "__main__":
    # When run by the backend, this generates the model
    doc = generate_model()
    print("SUCCESS: Model generation complete")
    # Don't call sys.exit() - let the backend handle STL export
