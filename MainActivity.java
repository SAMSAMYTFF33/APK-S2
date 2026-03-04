package com.S2;

import android.os.Bundle;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class MainActivity extends AppCompatActivity {
	
	private WebView webView;
	private ProgressBar progressBar;
	private File appFilesDir;
	
	// قائمة بالامتدادات المسموح بنسخها
	private static final Set<String> ALLOWED_EXTENSIONS = new HashSet<>(Arrays.asList( ".html", ".htm", ".js", ".json" ));
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		
		webView = findViewById(R.id.webView);
		progressBar = findViewById(R.id.progressBar);
		
		appFilesDir = getExternalFilesDir(null);
		
		// نسخ ملفات HTML, JS, JSON فقط من Assets إلى مجلد التطبيق لأول مرة
		copyAllowedAssetsToExternal();
		
		// إعداد WebView
		setupWebView();
		
		// تحميل الصفحة الرئيسية فقط
		loadLocalHtml("green.html"); // ✅ الصفحة الرئيسية ثابتة
	}
	
	private void setupWebView() {
		webView.getSettings().setJavaScriptEnabled(true);
		webView.getSettings().setAllowFileAccess(true);
		webView.getSettings().setDomStorageEnabled(true);
		
		webView.addJavascriptInterface(new Object() {
			@JavascriptInterface
			public void checkForUpdate() {
				runOnUiThread(() -> checkForUpdates());
			}
		}, "AndroidBridge");
		
		webView.setWebViewClient(new WebViewClient() {
			@Override
			public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
				progressBar.setVisibility(android.view.View.VISIBLE);
			}
			
			@Override
			public void onPageFinished(WebView view, String url) {
				progressBar.setVisibility(android.view.View.GONE);
			}
		});
		
		webView.setWebChromeClient(new WebChromeClient() {
			@Override
			public void onProgressChanged(WebView view, int newProgress) {
				if (newProgress < 100) progressBar.setProgress(newProgress);
			}
		});
	}
	
	private void loadLocalHtml(String fileName) {
		File file = new File(appFilesDir, fileName);
		if (file.exists()) {
			webView.loadUrl("file://" + file.getAbsolutePath());
			} else {
			webView.loadUrl("file:///android_asset/" + fileName);
		}
	}
	
	/**
	* نسخ الملفات المسموح بها فقط (HTML, JS, JSON) من مجلد assets
	*/
	private void copyAllowedAssetsToExternal() {
		try {
			copyAssetsRecursively(""); // نبدأ من المجلد الجذر
			} catch (IOException e) {
			e.printStackTrace();
			Log.e("FileCopy", "خطأ في نسخ الملفات: " + e.getMessage());
		}
	}
	
	/**
	* نسخ الملفات والمجلدات بشكل متكرر من assets مع فلتر الامتدادات
	* @param path المسار الحالي داخل مجلد assets
	*/
	private void copyAssetsRecursively(String path) throws IOException {
		String[] assets;
		try {
			assets = getAssets().list(path);
			if (assets == null || assets.length == 0) {
				return; // مجلد فارغ أو ملف وليس مجلد
			}
			} catch (IOException e) {
			// قد يكون المسار ملف وليس مجلد
			handleAssetFile(path);
			return;
		}
		
		// إنشاء المجلد المقابل في الوجهة
		File destDir = new File(appFilesDir, path);
		if (!destDir.exists()) {
			destDir.mkdirs();
		}
		
		// معالجة كل عنصر في المجلد الحالي
		for (String asset : assets) {
			String assetPath = path.isEmpty() ? asset : path + File.separator + asset;
			
			try {
				// التحقق مما إذا كان هذا المسار يمثل مجلداً
				String[] subAssets = getAssets().list(assetPath);
				if (subAssets != null && subAssets.length > 0) {
					// هذا مجلد، نواصل النسخ المتكرر
					copyAssetsRecursively(assetPath);
					} else {
					// هذا ملف، نتحقق من الامتداد قبل النسخ
					handleAssetFile(assetPath);
				}
				} catch (IOException e) {
				// في حالة الخطأ، نعتبره ملفاً ونحاول نسخه
				handleAssetFile(assetPath);
			}
		}
	}
	
	/**
	* معالجة ملف واحد من assets - نسخه فقط إذا كان له امتداد مسموح به
	* @param assetPath مسار الملف داخل assets
	*/
	private void handleAssetFile(String assetPath) {
		// التحقق من الامتداد
		if (isAllowedFile(assetPath)) {
			copySingleFile(assetPath);
			} else {
			Log.d("FileCopy", "تخطي الملف (غير مسموح): " + assetPath);
		}
	}
	
	/**
	* التحقق مما إذا كان الملف له امتداد مسموح به
	*/
	private boolean isAllowedFile(String filename) {
		String lowerName = filename.toLowerCase();
		for (String extension : ALLOWED_EXTENSIONS) {
			if (lowerName.endsWith(extension)) {
				return true;
			}
		}
		return false;
	}
	
	/**
	* نسخ ملف واحد من assets إلى المجلد الخارجي
	*/
	private void copySingleFile(String assetPath) {
		File destFile = new File(appFilesDir, assetPath);
		
		// إنشاء المجلدات الفرعية إذا لزم الأمر
		File parentDir = destFile.getParentFile();
		if (parentDir != null && !parentDir.exists()) {
			parentDir.mkdirs();
		}
		
		// نسخ الملف إذا لم يكن موجوداً (أو يمكنك إزالة الشرط لنسخه دائماً)
		if (!destFile.exists()) {
			try (InputStream in = getAssets().open(assetPath);
			OutputStream out = new FileOutputStream(destFile)) {
				
				byte[] buffer = new byte[1024];
				int read;
				while ((read = in.read(buffer)) != -1) {
					out.write(buffer, 0, read);
				}
				Log.d("FileCopy", "تم نسخ: " + assetPath);
				
				} catch (IOException e) {
				Log.e("FileCopy", "فشل نسخ " + assetPath + ": " + e.getMessage());
			}
			} else {
			Log.d("FileCopy", "الملف موجود مسبقاً: " + assetPath);
		}
	}
	
	private void checkForUpdates() {
		Toast.makeText(this, "جاري التحقق من التحديثات...", Toast.LENGTH_SHORT).show();
		
		GitHubUpdateChecker.checkForUpdates(this, appFilesDir, new GitHubUpdateChecker.UpdateCallback() {
			@Override
			public void onProgress(int progress) {
				runOnUiThread(() -> progressBar.setProgress(progress));
			}
			
			@Override
			public void onUpdateFound() {
				runOnUiThread(() -> {
					Toast.makeText(MainActivity.this, "✅ تم التحديث بنجاح!", Toast.LENGTH_SHORT).show();
					// لا نغير الصفحة الرئيسية، فقط نسمح للملفات الفرعية بأن تُفتح من روابط الصفحة الرئيسية
				});
			}
			
			@Override
			public void onNoUpdate() {
				runOnUiThread(() -> Toast.makeText(MainActivity.this, "ℹ️ لا توجد تحديثات", Toast.LENGTH_SHORT).show());
			}
			
			@Override
			public void onError(String error) {
				runOnUiThread(() -> Toast.makeText(MainActivity.this, "❌ خطأ: " + error, Toast.LENGTH_SHORT).show());
			}
		});
	}
	
	@Override
	public void onBackPressed() {
		if (webView.canGoBack()) webView.goBack();
		else super.onBackPressed();
	}
}