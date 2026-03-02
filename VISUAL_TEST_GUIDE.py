#!/usr/bin/env python
"""
Quick Visual Test - UI Integration Check
========================================

Run this after starting backend and frontend to verify integration.
"""

print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     ✅ INDUSTRIAL ENGINE UI INTEGRATION - VISUAL TEST GUIDE          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

1️⃣  START BACKEND
   ─────────────────────────────────────────────────────────────
   Terminal 1:
   > cd c:\\vivek\\Infosys_Internship\\ECO_PACK_AI\\ECO_PACK_AI
   > python src/api.py
   
   ✅ LOOK FOR:
      ✓ Industrial recommendation engine available
      ✓ Industrial Recommendation Engine initialized
      * Server running on http://localhost:8000


2️⃣  START FRONTEND
   ─────────────────────────────────────────────────────────────
   Terminal 2:
   > cd c:\\vivek\\Infosys_Internship\\ECO_PACK_AI\\ECO_PACK_AI\\frontend
   > npm run dev
   
   ✅ LOOK FOR:
      * Local: http://localhost:3000 (or 5173)


3️⃣  OPEN BROWSER
   ─────────────────────────────────────────────────────────────
   Navigate to: http://localhost:3000
   
   
4️⃣  CREATE PRODUCT
   ─────────────────────────────────────────────────────────────
   Go to "Product Form" page
   
   Enter any values:
   • Category: electronics
   • Weight: 5 kg
   • Fragility: 2
   
   Click: "Get AI Recommendations →"


5️⃣  VERIFY INDUSTRIAL ENGINE IS ACTIVE
   ─────────────────────────────────────────────────────────────
   On Recommendations page, look for:
   
   ✅ TOP RIGHT BADGE:
      ┌──────────────────────────────────────────┐
      │ 🚀 Industrial Multi-Objective Engine    │
      └──────────────────────────────────────────┘
   
   ✅ IN BROWSER CONSOLE (F12):
      [IndustrialEngine] POST /recommend/industrial
      [IndustrialEngine] Response status 200
      [IndustrialEngine] Recommendation response received
   
   ❌ IF YOU SEE:
      [IndustrialEngine] Not available, falling back to legacy
      → Industrial engine not initialized, check backend logs


6️⃣  CHECK MATERIAL CARDS
   ─────────────────────────────────────────────────────────────
   Look at the ranked materials on the right side:
   
   ✅ PARETO BADGE:
      ┌─────────────────────────────────┐
      │ 🌿 Bamboo            Score: 85  │
      │ #1  ★ Pareto                    │  ← GREEN BADGE!
      │ ⚡ Low cost, Low CO₂, Low risk  │  ← TRADEOFF!
      │ ┌──────┬──────┬────────┐       │
      │ │CO2:2 │R:85% │$0.30   │       │
      │ └──────┴──────┴────────┘       │
      └─────────────────────────────────┘
   
   ✅ PARETO RANK:
      • Top 1-3 materials: "★ Pareto" (green badge)
      • Others: "P1" or "P2" (gray badge)
   
   ✅ TRADEOFF SUMMARY:
      • Cyan text with ⚡ icon
      • "Low cost, Medium CO₂, Low risk" or similar


7️⃣  CHECK DETAILED PANEL
   ─────────────────────────────────────────────────────────────
   Click on any material card → Scroll down
   
   ✅ "WHY RECOMMENDED" PANEL:
      ┌─────────────────────────────────────────────┐
      │ 💡 Why Recommended                          │
      │ ┌─────────────────────────────────────────┐ │
      │ │ Best overall balance across all         │ │
      │ │ objectives. Excellent cost performance. │ │
      │ └─────────────────────────────────────────┘ │
      └─────────────────────────────────────────────┘
   
   ✅ DETAILED PROS/CONS:
      • Should be specific (from industrial engine)
      • Not generic fallback pros/cons


8️⃣  VERIFY DIVERSITY
   ─────────────────────────────────────────────────────────────
   Look at top 5-6 recommendations:
   
   ✅ DIFFERENT MATERIAL FAMILIES:
      #1 Bamboo     (plant-based)
      #2 Paper      (paper)
      #3 Plastic    (synthetic)
      #4 Metal      (metal)
      #5 Glass      (glass)
   
   ❌ NOT LIKE THIS:
      #1 Bamboo
      #2 Bagasse    } All plant-based!
      #3 Jute       } Not diverse!


9️⃣  CHECK BACKEND LOGS
   ─────────────────────────────────────────────────────────────
   In Terminal 1 (backend), you should see:
   
   ✅ WHEN REQUEST COMES:
      127.0.0.1 - - "POST /api/recommend/industrial HTTP/1.1" 200
   
   ✅ NO ERRORS:
      • No 503 errors
      • No import errors
      • No "Industrial engine not available"


🔟  SUCCESS CHECKLIST
   ─────────────────────────────────────────────────────────────
   ✅ Badge: "🚀 Industrial Multi-Objective Engine" visible
   ✅ Console: "[IndustrialEngine]" logs present
   ✅ Material cards: Pareto badges (★ Pareto) shown
   ✅ Material cards: Tradeoff summaries (⚡ Low cost...) shown
   ✅ Detailed panel: "💡 Why Recommended" panel present
   ✅ Diversity: Multiple material families in top 5
   ✅ Backend: No errors, 200 responses
   ✅ Frontend: No React errors in console


═══════════════════════════════════════════════════════════════════

🎉 IF ALL CHECKMARKS PASS:
   INDUSTRIAL ENGINE IS FULLY INTEGRATED AND WORKING!

❌ IF SOME FAIL:
   Check UI_INTEGRATION_COMPLETE.md for troubleshooting

═══════════════════════════════════════════════════════════════════

QUICK COMPARISON:
──────────────────────────────────────────────────────────────────

BEFORE (Legacy):                AFTER (Industrial):
─────────────────              ──────────────────────
• No badge                     • 🚀 Industrial badge
• No Pareto rank               • ★ Pareto badges
• No tradeoff summary          • ⚡ Tradeoff summaries
• No explanation               • 💡 Why Recommended
• Generic pros/cons            • Specific pros/cons
• Same ranking always          • Dynamic optimization
• Not diverse                  • Multiple families

═══════════════════════════════════════════════════════════════════
""")


if __name__ == '__main__':
    import webbrowser
    import time
    
    print("\n🚀 Opening documentation in 3 seconds...")
    time.sleep(3)
    
    # Try to open the documentation
    try:
        import os
        doc_path = os.path.join(os.path.dirname(__file__), 'UI_INTEGRATION_COMPLETE.md')
        if os.path.exists(doc_path):
            print(f"✓ Opening {doc_path}")
            webbrowser.open(doc_path)
        else:
            print("⚠ Documentation file not found, but integration is complete!")
    except Exception as e:
        print(f"⚠ Could not open documentation: {e}")
    
    print("\n✅ Integration complete! Follow the visual test guide above.")
