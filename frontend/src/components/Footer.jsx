import React from 'react';
import { motion } from 'framer-motion';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative z-10 border-t border-white/5 backdrop-blur-sm bg-slate-950/40">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="space-y-8"
        >
          {/* Main Footer Content */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 pb-8">
            {/* Brand & Mission */}
            <div>
              <h3 className="text-sm font-semibold text-white mb-3">ECO_PACK_AI</h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                Industrial-grade AI for sustainable packaging optimization. Multi-objective intelligence for real-world impact.
              </p>
            </div>

            {/* Product Links */}
            <div>
              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-4">Products</h4>
              <ul className="space-y-2 text-xs text-gray-500">
                <li><a href="#demo" className="hover:text-gray-300 transition-colors">Live Demo</a></li>
                <li><a href="#features" className="hover:text-gray-300 transition-colors">Features</a></li>
                <li><a href="#api" className="hover:text-gray-300 transition-colors">API</a></li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-4">Resources</h4>
              <ul className="space-y-2 text-xs text-gray-500">
                <li><a href="#docs" className="hover:text-gray-300 transition-colors">Documentation</a></li>
                <li><a href="#validation" className="hover:text-gray-300 transition-colors">Validation</a></li>
                <li><a href="#status" className="hover:text-gray-300 transition-colors">System Status</a></li>
              </ul>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

          {/* Bottom Footer */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Copyright */}
            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
              className="text-xs text-gray-600"
            >
              © {currentYear} ECO_PACK_AI. All rights reserved.
            </motion.p>

            {/* Developer Credit */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="flex items-center gap-2 text-xs text-gray-600"
            >
              <span>Developed by</span>
              <a
                href="#"
                className="font-medium text-gray-400 hover:text-gray-200 transition-colors"
              >
                Vivek Marri
              </a>
            </motion.div>

            {/* Legal Links */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              viewport={{ once: true }}
              className="flex items-center gap-4 text-xs text-gray-600"
            >
              <a href="#privacy" className="hover:text-gray-400 transition-colors">Privacy</a>
              <div className="w-px h-3 bg-gray-700" />
              <a href="#terms" className="hover:text-gray-400 transition-colors">Terms</a>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </footer>
  );
}
