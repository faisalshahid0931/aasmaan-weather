package pk.aasmaan.weather;

import android.Manifest;
import android.app.Activity;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.HashMap;

public class MainActivity extends Activity {
    static final String HOST = "app.aasmaan.invalid";
    static final String BASE = "https://" + HOST + "/";
    static final int REQ_LOC = 1, REQ_NOTIF = 2;
    WebView wv;
    GeolocationPermissions.Callback geoCb;
    String geoOrigin;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        int bg = Color.parseColor("#070a1c");
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        wv = new WebView(this);
        wv.setBackgroundColor(bg);
        setContentView(wv);
        WebSettings s = wv.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setGeolocationEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setTextZoom(100);
        wv.addJavascriptInterface(new Bridge(), "AasmaanApp");
        wv.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                return serve(r.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView v, String url) {
                Uri u = Uri.parse(url);
                if (HOST.equals(u.getHost())) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception e) { }
                return true;
            }
        });
        wv.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                if (hasLoc()) {
                    cb.invoke(origin, true, false);
                } else {
                    geoCb = cb;
                    geoOrigin = origin;
                    requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, REQ_LOC);
                }
            }
        });
        wv.loadUrl(BASE + "index.html");
    }

    boolean hasLoc() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] res) {
        if (code == REQ_LOC && geoCb != null) {
            boolean ok = false;
            for (int r : res) if (r == PackageManager.PERMISSION_GRANTED) ok = true;
            geoCb.invoke(geoOrigin, ok, false);
            geoCb = null;
        }
    }

    WebResourceResponse serve(Uri u) {
        if (!HOST.equals(u.getHost())) return null;
        String p = u.getPath();
        if (p == null || p.equals("/")) p = "/index.html";
        p = p.substring(1);
        try {
            InputStream in = getAssets().open(p);
            return new WebResourceResponse(mime(p), "UTF-8", in);
        } catch (Exception e) {
            return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found",
                    new HashMap<String, String>(), new ByteArrayInputStream(new byte[0]));
        }
    }

    static String mime(String p) {
        if (p.endsWith(".html")) return "text/html";
        if (p.endsWith(".js")) return "application/javascript";
        if (p.endsWith(".css")) return "text/css";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".woff2")) return "font/woff2";
        if (p.endsWith(".webmanifest") || p.endsWith(".json")) return "application/json";
        return "application/octet-stream";
    }

    @Override
    public void onBackPressed() {
        String js = "(function(){var p=document.getElementById('panel'),s=document.getElementById('sheet');"
                + "if(p&&p.classList.contains('open')){p.classList.remove('open');return 1}"
                + "if(s&&s.classList.contains('open')){s.classList.remove('open');return 1}return 0})()";
        wv.evaluateJavascript(js, new ValueCallback<String>() {
            @Override
            public void onReceiveValue(String v) {
                if (!"1".equals(v)) MainActivity.this.finish();
            }
        });
    }

    @Override
    protected void onPause() { super.onPause(); wv.onPause(); }

    @Override
    protected void onResume() { super.onResume(); wv.onResume(); }

    @Override
    protected void onDestroy() { wv.destroy(); super.onDestroy(); }

    class Bridge {
        @JavascriptInterface
        public void share(final String text) {
            runOnUiThread(new Runnable() {
                public void run() {
                    Intent i = new Intent(Intent.ACTION_SEND);
                    i.setType("text/plain");
                    i.putExtra(Intent.EXTRA_TEXT, text);
                    startActivity(Intent.createChooser(i, "Share forecast"));
                }
            });
        }

        @JavascriptInterface
        public boolean canNotify() {
            return Build.VERSION.SDK_INT < 33
                    || checkSelfPermission("android.permission.POST_NOTIFICATIONS") == PackageManager.PERMISSION_GRANTED;
        }

        @JavascriptInterface
        public void askNotify() {
            if (!canNotify()) {
                runOnUiThread(new Runnable() {
                    public void run() {
                        requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, REQ_NOTIF);
                    }
                });
            }
        }

        @JavascriptInterface
        public void notify(final String title, final String body) {
            if (!canNotify()) return;
            NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            Notification.Builder nb = new Notification.Builder(MainActivity.this);
            try {
                if (Build.VERSION.SDK_INT >= 26) {
                    Class<?> cc = Class.forName("android.app.NotificationChannel");
                    Object ch = cc.getConstructor(String.class, CharSequence.class, int.class).newInstance("wx", "Weather alerts", 3);
                    nm.getClass().getMethod("createNotificationChannel", cc).invoke(nm, ch);
                    nb.getClass().getMethod("setChannelId", String.class).invoke(nb, "wx");
                }
            } catch (Exception e) { }
            Intent open = new Intent(MainActivity.this, MainActivity.class);
            open.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            int fl = PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0);
            nb.setSmallIcon(R.drawable.ic_stat)
              .setContentTitle(title)
              .setContentText(body)
              .setStyle(new Notification.BigTextStyle().bigText(body))
              .setAutoCancel(true)
              .setContentIntent(PendingIntent.getActivity(MainActivity.this, 0, open, fl));
            nm.notify(1, nb.build());
        }
    }
}
