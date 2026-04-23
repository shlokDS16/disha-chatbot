import type { Language } from "../api/types";

type Strings = Record<string, { en: string; hi: string; mr: string }>;

const DICT: Strings = {
  appName: { en: "Disha", hi: "दिशा", mr: "दिशा" },
  tagline: {
    en: "Your genetic counselling companion",
    hi: "आपका जेनेटिक काउंसलिंग साथी",
    mr: "तुमचा जनुकीय समुपदेशन सोबती",
  },
  nav_chat: { en: "Chat", hi: "चैट", mr: "चॅट" },
  nav_docs: { en: "Document scanner", hi: "दस्तावेज़ स्कैनर", mr: "दस्तऐवज स्कॅनर" },
  nav_tips: { en: "Health tips", hi: "स्वास्थ्य सुझाव", mr: "आरोग्य टिप्स" },
  nav_maps: { en: "Nearby care", hi: "नज़दीकी देखभाल", mr: "जवळील सेवा" },
  nav_consent: { en: "Consent & privacy", hi: "सहमति व गोपनीयता", mr: "संमती व गोपनीयता" },
  nav_about: { en: "About Disha", hi: "दिशा के बारे में", mr: "दिशा बद्दल" },

  composer_placeholder: {
    en: "Ask about sickle cell, reports, or nearby centres…",
    hi: "सिकल सेल, रिपोर्ट या नज़दीकी केंद्रों के बारे में पूछें…",
    mr: "सिकल सेल, अहवाल किंवा जवळील केंद्रांबद्दल विचारा…",
  },
  send: { en: "Send", hi: "भेजें", mr: "पाठवा" },
  mic: { en: "Speak", hi: "बोलें", mr: "बोला" },
  attach: { en: "Attach report", hi: "रिपोर्ट जोड़ें", mr: "अहवाल जोडा" },
  listening: { en: "Listening…", hi: "सुन रहे हैं…", mr: "ऐकत आहे…" },
  thinking: { en: "Disha is thinking…", hi: "दिशा सोच रही है…", mr: "दिशा विचार करत आहे…" },

  hello_hero_a: {
    en: "Namaste 🙏",
    hi: "नमस्ते 🙏",
    mr: "नमस्कार 🙏",
  },
  hello_hero_b: {
    en: "I'm Disha. I help ASHA workers, families and doctors understand sickle cell — in simple words, in your language.",
    hi: "मैं दिशा हूँ। मैं आशा कार्यकर्ताओं, परिवारों और डॉक्टरों को सिकल सेल को सरल भाषा में समझाती हूँ — आपकी भाषा में।",
    mr: "मी दिशा आहे. मी आशा कार्यकर्त्या, कुटुंबे व डॉक्टरांना सिकल सेल सोप्या भाषेत समजावून सांगते — तुमच्या भाषेत.",
  },

  suggested: { en: "Try asking", hi: "यह पूछकर देखें", mr: "हे विचारून पहा" },
  location_ask_title: {
    en: "May we use your location?",
    hi: "क्या हम आपकी लोकेशन ले सकते हैं?",
    mr: "आम्ही तुमचे स्थान वापरू शकतो का?",
  },
  location_ask_body: {
    en: "So when you ask for the nearest HPLC centre or hospital, the answer is instant.",
    hi: "ताकि जब आप नज़दीकी HPLC केंद्र या अस्पताल पूछें, जवाब तुरंत मिले।",
    mr: "जेणेकरून तुम्ही जवळचे HPLC केंद्र किंवा रुग्णालय विचारताच उत्तर लगेच मिळेल.",
  },
  location_allow: { en: "Use my location", hi: "लोकेशन दें", mr: "स्थान द्या" },
  location_skip: { en: "Not now", hi: "अभी नहीं", mr: "आत्ता नको" },
  location_set: {
    en: "Location saved",
    hi: "लोकेशन सुरक्षित",
    mr: "स्थान जतन केले",
  },
  location_denied: {
    en: "Location not shared — map queries will ask for it.",
    hi: "लोकेशन नहीं दी गई — मैप क्वेरी में पूछा जाएगा।",
    mr: "स्थान दिले नाही — नकाशा प्रश्नात विचारले जाईल.",
  },

  consent_title: {
    en: "Before we begin",
    hi: "शुरू करने से पहले",
    mr: "सुरु करण्यापूर्वी",
  },
  consent_body: {
    en: "Disha stores your chat on this device so you can come back to it. Nothing is shared without permission. You can delete everything anytime.",
    hi: "दिशा आपकी बातचीत इसी डिवाइस पर रखती है ताकि आप बाद में देख सकें। बिना अनुमति कुछ भी साझा नहीं होता। आप कभी भी सब मिटा सकते हैं।",
    mr: "दिशा तुमची चॅट याच डिव्हाइसवर ठेवते जेणेकरून तुम्ही नंतर पाहू शकता. परवानगीशिवाय काहीही शेअर होत नाही. तुम्ही कधीही सर्व पुसू शकता.",
  },
  consent_accept: { en: "I agree — start chatting", hi: "सहमत हूँ — बातचीत शुरू", mr: "सहमत आहे — चॅट सुरू" },
  consent_decline: { en: "Not now", hi: "अभी नहीं", mr: "आत्ता नको" },

  new_chat: { en: "New chat", hi: "नई चैट", mr: "नवीन चॅट" },
  you: { en: "You", hi: "आप", mr: "तुम्ही" },
  disha: { en: "Disha", hi: "दिशा", mr: "दिशा" },
  source_rag: { en: "Verified knowledge", hi: "सत्यापित जानकारी", mr: "सत्यापित माहिती" },
  source_llm: { en: "Generated answer", hi: "AI उत्तर", mr: "AI उत्तर" },
  source_hybrid: { en: "Knowledge + AI", hi: "ज्ञान + AI", mr: "ज्ञान + AI" },
  source_tool: { en: "Calculated", hi: "गणना किया", mr: "गणना केले" },

  empty_docs_title: {
    en: "Upload a report to scan",
    hi: "रिपोर्ट अपलोड करें",
    mr: "अहवाल अपलोड करा",
  },
  empty_docs_body: {
    en: "PDF, image or DOCX. We read it carefully and explain in simple words.",
    hi: "PDF, इमेज या DOCX। हम इसे ध्यान से पढ़कर सरल भाषा में बताते हैं।",
    mr: "PDF, इमेज किंवा DOCX. आम्ही ते काळजीपूर्वक वाचून सोप्या भाषेत सांगतो.",
  },
  upload_cta: { en: "Choose file", hi: "फ़ाइल चुनें", mr: "फाइल निवडा" },

  maps_title: { en: "Nearest care centres", hi: "नज़दीकी देखभाल केंद्र", mr: "जवळील सेवा केंद्र" },
  maps_service: { en: "Service", hi: "सेवा", mr: "सेवा" },
  maps_refresh: { en: "Refresh", hi: "ताज़ा करें", mr: "रिफ्रेश" },
  maps_directions: { en: "Directions", hi: "रास्ता", mr: "मार्गदर्शन" },
  maps_km: { en: "km away", hi: "किमी दूर", mr: "किमी दूर" },
  maps_open_now: { en: "Open now", hi: "अभी खुला", mr: "आता सुरू" },
  maps_closed: { en: "Closed", hi: "बंद", mr: "बंद" },
  maps_service_any: { en: "Any", hi: "कोई भी", mr: "कोणतेही" },
  maps_service_hplc: { en: "HPLC centre", hi: "HPLC केंद्र", mr: "HPLC केंद्र" },
  maps_service_cvs: { en: "CVS / amnio", hi: "CVS / amnio", mr: "CVS / amnio" },
  maps_service_haem: { en: "Haematology", hi: "हेमेटोलॉजी", mr: "रक्तविज्ञान" },
  maps_service_hu: { en: "Hydroxyurea dispensing", hi: "हाइड्रोक्सीयूरिया", mr: "हायड्रॉक्सीयुरिया" },
  maps_service_hospital: { en: "General hospital", hi: "सामान्य अस्पताल", mr: "सामान्य रुग्णालय" },

  about_title: { en: "About Disha", hi: "दिशा के बारे में", mr: "दिशा बद्दल" },
  about_body: {
    en: "Disha is a free, private companion for sickle cell awareness in tribal Maharashtra. Built for ASHA workers, at-risk couples, patients and doctors. Answers come from vetted knowledge plus careful AI.",
    hi: "दिशा आदिवासी महाराष्ट्र में सिकल सेल जागरूकता के लिए एक नि:शुल्क, निजी साथी है। आशा कार्यकर्ताओं, जोखिम वाले जोड़ों, मरीज़ों और डॉक्टरों के लिए।",
    mr: "दिशा हा आदिवासी महाराष्ट्रातील सिकल सेल जागरूकतेसाठी मोफत, खाजगी सोबती आहे. आशा कार्यकर्त्या, जोखमीची जोडपी, रुग्ण व डॉक्टरांसाठी.",
  },

  delete_all: { en: "Delete my data", hi: "मेरा डेटा मिटाएँ", mr: "माझा डेटा पुसा" },
  delete_confirm: {
    en: "This will remove all chats, files and reports from this device. Continue?",
    hi: "यह इस डिवाइस से सभी बातचीत, फ़ाइलें और रिपोर्ट हटा देगा। जारी रखें?",
    mr: "हे या डिव्हाइसमधून सर्व चॅट, फायली व अहवाल काढून टाकेल. सुरू ठेवायचे?",
  },

  feedback_helpful: { en: "Helpful", hi: "मददगार", mr: "उपयोगी" },
  feedback_not: { en: "Not helpful", hi: "मददगार नहीं", mr: "उपयोगी नाही" },
  play_audio: { en: "Play", hi: "चलाएँ", mr: "वाजवा" },
  pause_audio: { en: "Pause", hi: "रोकें", mr: "थांबवा" },

  persona_asha: { en: "ASHA worker", hi: "आशा कार्यकर्ता", mr: "आशा कार्यकर्ती" },
  persona_couple: { en: "Couple planning", hi: "जोड़ा / परिवार", mr: "जोडपे / कुटुंब" },
  persona_patient: { en: "Patient / family", hi: "मरीज़ / परिवार", mr: "रुग्ण / कुटुंब" },
  persona_doctor: { en: "Doctor", hi: "डॉक्टर", mr: "डॉक्टर" },
  persona_pick: { en: "Who is asking?", hi: "कौन पूछ रहे हैं?", mr: "कोण विचारत आहे?" },

  lang_en: { en: "English", hi: "English", mr: "English" },
  lang_hi: { en: "हिन्दी", hi: "हिन्दी", mr: "हिन्दी" },
  lang_mr: { en: "मराठी", hi: "मराठी", mr: "मराठी" },

  tips_title: { en: "Everyday health tips", hi: "रोज़मर्रा के स्वास्थ्य सुझाव", mr: "दैनंदिन आरोग्य सल्ले" },
  crisis_title: { en: "Helplines", hi: "हेल्पलाइन", mr: "हेल्पलाइन" },

  file_summary_title: {
    en: "Document summary",
    hi: "दस्तावेज़ सारांश",
    mr: "दस्तऐवज सारांश",
  },
  file_detailed_analysis: {
    en: "What the document says",
    hi: "दस्तावेज़ क्या कहता है",
    mr: "दस्तऐवज काय सांगतो",
  },
  file_what_it_means: {
    en: "What this means for you",
    hi: "आपके लिए इसका मतलब",
    mr: "तुमच्यासाठी याचा अर्थ",
  },
  file_next_steps: {
    en: "Next steps",
    hi: "आगे के कदम",
    mr: "पुढील पावले",
  },
  file_show_text: {
    en: "Show extracted text",
    hi: "निकाला गया टेक्स्ट दिखाएँ",
    mr: "काढलेला मजकूर दाखवा",
  },
  file_hide_text: {
    en: "Hide extracted text",
    hi: "टेक्स्ट छिपाएँ",
    mr: "मजकूर लपवा",
  },
  file_processing: {
    en: "Reading your document…",
    hi: "आपका दस्तावेज़ पढ़ रही हूँ…",
    mr: "तुमचा दस्तऐवज वाचत आहे…",
  },
  file_failed: {
    en: "Sorry, I couldn't read that file. Please try again.",
    hi: "क्षमा करें, मैं फ़ाइल नहीं पढ़ पाई। कृपया फिर से कोशिश करें।",
    mr: "माफ करा, मला ती फाइल वाचता आली नाही. पुन्हा प्रयत्न करा.",
  },

  history_title: { en: "Your chats", hi: "आपकी बातचीत", mr: "तुमच्या चॅट्स" },
  history_empty: {
    en: "No chats yet. Start one below!",
    hi: "अभी कोई बातचीत नहीं। नीचे शुरू करें!",
    mr: "अजून कोणतीही चॅट नाही. खाली सुरू करा!",
  },
  history_delete_all: {
    en: "Clear all chats",
    hi: "सभी चैट हटाएँ",
    mr: "सर्व चॅट्स पुसा",
  },
  history_share: { en: "Share chat", hi: "चैट साझा करें", mr: "चॅट शेअर करा" },
  history_export: { en: "Export as text", hi: "टेक्स्ट में सहेजें", mr: "मजकूर म्हणून जतन करा" },
  history_copy: { en: "Copy to clipboard", hi: "क्लिपबोर्ड पर कॉपी", mr: "क्लिपबोर्डवर कॉपी" },
  history_copied: { en: "Copied!", hi: "कॉपी हो गया!", mr: "कॉपी केले!" },
  history_delete_confirm: {
    en: "Delete this chat history? This cannot be undone.",
    hi: "इस चैट को हटाएँ? यह पूर्ववत नहीं हो सकता।",
    mr: "ही चॅट पुसायची? हे परत आणता येणार नाही.",
  },

  faq_always_title: {
    en: "Common questions",
    hi: "सामान्य सवाल",
    mr: "नेहमीचे प्रश्न",
  },

  theme_light: { en: "Light", hi: "लाइट", mr: "लाइट" },
  theme_dark: { en: "Dark", hi: "डार्क", mr: "डार्क" },
  theme_toggle: {
    en: "Toggle light/dark mode",
    hi: "लाइट/डार्क मोड बदलें",
    mr: "लाइट/डार्क मोड बदला",
  },
};

export function t(key: string, lang: Language): string {
  const entry = DICT[key];
  if (!entry) return key;
  return entry[lang] ?? entry.en;
}
