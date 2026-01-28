import React, { useState, useEffect } from 'react';

/**
 * Splash Screen do MotoFlash
 *
 * IMPORTANTE: Este componente usa fundo transparente.
 * Adicione no HTML onde for usar este componente:
 *
 * <div class="background-image">
 *   <img src="/static/fundo/cidade_3.jpg" alt="City Background">
 * </div>
 *
 * E o CSS do fundo (igual ao login):
 *
 * .background-image {
 *   position: fixed;
 *   top: 0;
 *   left: 0;
 *   width: 100%;
 *   height: 100%;
 *   z-index: 0;
 * }
 * .background-image img {
 *   width: 100%;
 *   height: 100%;
 *   object-fit: cover;
 *   object-position: center bottom;
 *   filter: brightness(0.75) saturate(1.1);
 * }
 * .background-image::after {
 *   content: '';
 *   position: absolute;
 *   top: 0;
 *   left: 0;
 *   width: 100%;
 *   height: 100%;
 *   background: linear-gradient(
 *     180deg,
 *     rgba(10, 10, 15, 0.2) 0%,
 *     rgba(10, 10, 15, 0.1) 50%,
 *     rgba(10, 10, 15, 0.4) 100%
 *   );
 * }
 */
export default function MotoFlashSplash({ restaurantName = "seu restaurante" }) {
  const [showSplash, setShowSplash] = useState(true);
  const [fadeOut, setFadeOut] = useState(false);
  const [key, setKey] = useState(0);

  useEffect(() => {
    const fadeTimer = setTimeout(() => setFadeOut(true), 3500);
    const hideTimer = setTimeout(() => setShowSplash(false), 4000);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(hideTimer);
    };
  }, [key]);

  const restart = () => {
    setShowSplash(true);
    setFadeOut(false);
    setKey(k => k + 1);
  };

  if (!showSplash) {
    return (
      <div className="main-content">
        <h1>⚡ Bem-vindo ao MotoFlash!</h1>
        <p>Dashboard carregado com sucesso</p>
        <button onClick={restart} className="restart-btn">
          ↻ Ver splash novamente
        </button>

        <style>{`
          .main-content {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: transparent;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            gap: 12px;
            position: relative;
            z-index: 10;
          }
          .main-content h1 { font-size: 28px; font-weight: 700; margin: 0; }
          .main-content p { font-size: 16px; color: rgba(255,255,255,0.9); margin: 0; }
          .restart-btn {
            margin-top: 24px;
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 50px;
            color: #f97316;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
          }
          .restart-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className={`splash-container ${fadeOut ? 'fade-out' : ''}`}>
      <div className="background" />
      
      {/* Mini raios sutis flutuando */}
      <div className="mini-bolts">
        <svg className="mini-bolt b1" viewBox="0 0 24 24">
          <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" fill="rgba(255,255,255,0.15)"/>
        </svg>
        <svg className="mini-bolt b2" viewBox="0 0 24 24">
          <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" fill="rgba(255,255,255,0.12)"/>
        </svg>
        <svg className="mini-bolt b3" viewBox="0 0 24 24">
          <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" fill="rgba(255,255,255,0.1)"/>
        </svg>
        <svg className="mini-bolt b4" viewBox="0 0 24 24">
          <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" fill="rgba(255,255,255,0.08)"/>
        </svg>
      </div>

      {/* Linhas de energia sutis */}
      <div className="energy-lines">
        <div className="energy-line l1" />
        <div className="energy-line l2" />
        <div className="energy-line l3" />
      </div>

      <div className="logo-wrapper">
        <div className="glow" />
        
        {/* Logo - Círculo laranja com raio branco (igual ao logo real) */}
        <div className="logo-circle">
          <svg viewBox="0 0 80 80" className="bolt-icon">
            <path
              d="M44 12 L28 40 L38 40 L32 68 L56 36 L44 36 L52 12 Z"
              fill="white"
            />
          </svg>
        </div>

        <h1 className="brand-name">
          <span className="brand-moto">Moto</span>
          <span className="brand-flash">Flash</span>
        </h1>

        <p className="tagline">Bem-vindo de volta, {restaurantName}!</p>

        <div className="loading-dots">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>

        <div className="loading-container">
          <div className="loading-track">
            <div className="loading-bar" key={key} />
          </div>
        </div>
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-8px) rotate(1deg); }
        }
        
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes loadingProgress {
          0% { width: 0%; }
          100% { width: 100%; }
        }
        
        @keyframes dotPulse {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        
        @keyframes miniBoltFloat1 {
          0%, 100% { transform: translate(0, 0) rotate(-15deg) scale(1); opacity: 0.15; }
          50% { transform: translate(10px, -20px) rotate(-10deg) scale(1.1); opacity: 0.25; }
        }
        
        @keyframes miniBoltFloat2 {
          0%, 100% { transform: translate(0, 0) rotate(20deg) scale(1); opacity: 0.12; }
          50% { transform: translate(-15px, -15px) rotate(25deg) scale(0.9); opacity: 0.2; }
        }
        
        @keyframes miniBoltFloat3 {
          0%, 100% { transform: translate(0, 0) rotate(-25deg) scale(1); opacity: 0.1; }
          50% { transform: translate(8px, 15px) rotate(-20deg) scale(1.05); opacity: 0.18; }
        }
        
        @keyframes miniBoltFloat4 {
          0%, 100% { transform: translate(0, 0) rotate(10deg) scale(1); opacity: 0.08; }
          50% { transform: translate(-10px, 10px) rotate(15deg) scale(0.95); opacity: 0.15; }
        }
        
        @keyframes energyMove {
          0% { transform: translateX(-100%) scaleX(0.5); opacity: 0; }
          50% { opacity: 1; }
          100% { transform: translateX(200vw) scaleX(0.5); opacity: 0; }
        }
        
        @keyframes boltShine {
          0%, 100% { filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.4)); }
          50% { filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.8)); }
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); box-shadow: 0 10px 40px rgba(0,0,0,0.15), 0 0 0 8px rgba(255,255,255,0.1), 0 0 60px rgba(255, 107, 0, 0.4); }
          50% { transform: scale(1.05); box-shadow: 0 15px 50px rgba(0,0,0,0.2), 0 0 0 12px rgba(255,255,255,0.15), 0 0 80px rgba(255, 107, 0, 0.6); }
        }

        .splash-container {
          position: fixed;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          z-index: 9999;
          transition: opacity 0.5s ease-out;
        }
        
        .splash-container.fade-out { opacity: 0; }

        .background {
          position: absolute;
          inset: 0;
          background: transparent;
        }
        
        .mini-bolts {
          position: absolute;
          inset: 0;
          pointer-events: none;
        }
        
        .mini-bolt {
          position: absolute;
          width: 40px;
          height: 40px;
        }
        
        .mini-bolt.b1 {
          top: 15%;
          left: 10%;
          animation: miniBoltFloat1 4s ease-in-out infinite;
        }
        
        .mini-bolt.b2 {
          top: 20%;
          right: 12%;
          width: 50px;
          height: 50px;
          animation: miniBoltFloat2 5s ease-in-out infinite;
        }
        
        .mini-bolt.b3 {
          bottom: 25%;
          left: 8%;
          width: 35px;
          height: 35px;
          animation: miniBoltFloat3 4.5s ease-in-out infinite;
        }
        
        .mini-bolt.b4 {
          bottom: 18%;
          right: 15%;
          width: 45px;
          height: 45px;
          animation: miniBoltFloat4 5.5s ease-in-out infinite;
        }
        
        .energy-lines {
          position: absolute;
          inset: 0;
          overflow: hidden;
          pointer-events: none;
        }
        
        .energy-line {
          position: absolute;
          height: 2px;
          width: 100px;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), rgba(255,255,255,0.6), rgba(255,255,255,0.4), transparent);
          border-radius: 2px;
        }
        
        .energy-line.l1 {
          top: 30%;
          animation: energyMove 3s ease-in-out infinite;
        }
        
        .energy-line.l2 {
          top: 50%;
          width: 80px;
          animation: energyMove 3.5s ease-in-out infinite;
          animation-delay: 1s;
        }
        
        .energy-line.l3 {
          top: 70%;
          width: 120px;
          animation: energyMove 4s ease-in-out infinite;
          animation-delay: 2s;
        }
        
        .logo-wrapper {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
          z-index: 10;
          animation: fadeInUp 0.8s ease-out;
          position: relative;
        }
        
        .glow {
          position: absolute;
          width: 200px;
          height: 200px;
          background: radial-gradient(circle, rgba(255,255,255,0.25) 0%, transparent 70%);
          border-radius: 50%;
          top: -30px;
          pointer-events: none;
        }
        
        .logo-circle {
          width: 140px;
          height: 140px;
          background: #FF6B00;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow:
            0 10px 40px rgba(0,0,0,0.15),
            0 0 0 8px rgba(255,255,255,0.1),
            0 0 60px rgba(255, 107, 0, 0.4);
          animation: float 3s ease-in-out infinite, pulse 2s ease-in-out infinite;
        }
        
        .bolt-icon {
          width: 140px;
          height: 140px;
          animation: boltShine 2s ease-in-out infinite;
        }
        
        .brand-name {
          font-size: 44px;
          font-weight: 800;
          letter-spacing: -1px;
          margin: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .brand-moto { color: white; }
        .brand-flash {
          background: linear-gradient(135deg, #ff6b00 0%, #ff8c42 50%, #ffad42 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: 700;
        }
        
        .tagline {
          font-size: 15px;
          color: rgba(255,255,255,0.85);
          margin: 0;
          font-weight: 500;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .loading-dots {
          display: flex;
          gap: 8px;
          margin-top: 4px;
        }
        
        .dot {
          width: 8px;
          height: 8px;
          background: rgba(255,255,255,0.8);
          border-radius: 50%;
          animation: dotPulse 1.4s ease-in-out infinite;
        }
        
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        
        .loading-container {
          margin-top: 8px;
          width: 200px;
        }
        
        .loading-track {
          width: 100%;
          height: 4px;
          background: rgba(255,255,255,0.2);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .loading-bar {
          height: 100%;
          background: white;
          border-radius: 4px;
          animation: loadingProgress 3.5s ease-out forwards;
          box-shadow: 0 0 10px rgba(255,255,255,0.5);
        }
      `}</style>
    </div>
  );
}