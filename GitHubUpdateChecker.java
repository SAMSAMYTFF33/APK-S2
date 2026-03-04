package com.S2;

import android.content.Context;
import android.util.Log;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class GitHubUpdateChecker {
	
	private static final String TAG = "GitHubUpdateChecker";
	private static final String UPDATE_JSON_URL = "https://raw.githubusercontent.com/SAMSAMYTFF33/UPDATEFILE/main/update.json";
	
	public interface UpdateCallback {
		void onProgress(int progress);
		void onUpdateFound();
		void onNoUpdate();
		void onError(String error);
	}
	
	public static void checkForUpdates(Context context, File appFilesDir, UpdateCallback callback) {
		new Thread(() -> {
			try {
				// 1. الاتصال بـ GitHub وجلب ملف JSON (مع إضافة رقم عشوائي لتخطي الكاش)
				String noCacheUrl = UPDATE_JSON_URL + "?t=" + System.currentTimeMillis();
				URL url = new URL(noCacheUrl);
				HttpURLConnection conn = (HttpURLConnection) url.openConnection();
				conn.setRequestMethod("GET");
				
				if (conn.getResponseCode() != 200) {
					callback.onError("فشل الاتصال بالسيرفر: " + conn.getResponseCode());
					return;
				}
				
				BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
				StringBuilder sb = new StringBuilder();
				String line;
				while ((line = reader.readLine()) != null) sb.append(line);
				reader.close();
				
				JSONObject updateJson = new JSONObject(sb.toString());
				JSONArray filesArray = updateJson.getJSONArray("files");
				
				// 2. قراءة الإصدارات المحلية من ملف versions.json
				File versionsFile = new File(appFilesDir, "versions.json");
				JSONObject localVersions = new JSONObject();
				if (versionsFile.exists()) {
					BufferedReader vr = new BufferedReader(new FileReader(versionsFile));
					StringBuilder vrsb = new StringBuilder();
					String vLine;
					while ((vLine = vr.readLine()) != null) vrsb.append(vLine);
					vr.close();
					localVersions = new JSONObject(vrsb.toString());
				}
				
				boolean anyFileUpdated = false;
				int totalFiles = filesArray.length();
				
				for (int i = 0; i < totalFiles; i++) {
					JSONObject fileObj = filesArray.getJSONObject(i);
					String fileName = fileObj.getString("file_name");
					
					// ✅ التعديل هنا: استخدام getDouble بدلاً من getInt لدعم الأرقام العشرية (مثل 1.2)
					double latestVersion = fileObj.getDouble("latest_version_code");
					String htmlUrl = fileObj.getString("html_url");
					
					// ✅ التعديل هنا: استخدام optDouble
					double localVersion = localVersions.optDouble(fileName, 0.0);
					
					// 3. المقارنة: التحديث يتم فقط إذا كان إصدار GitHub أكبر من المحلي
					if (latestVersion > localVersion) {
						Log.d(TAG, "تحديث وجد للملف: " + fileName + " (من " + localVersion + " إلى " + latestVersion + ")");
						if (downloadFile(htmlUrl, new File(appFilesDir, fileName))) {
							// ✅ حفظ الرقم العشري الجديد
							localVersions.put(fileName, latestVersion);
							anyFileUpdated = true;
						}
					}
					
					int progressPercent = (int) (((i + 1) * 100.0f) / totalFiles);
					callback.onProgress(progressPercent);
				}
				
				// 4. حفظ أرقام الإصدارات الجديدة في الملف المحلي
				if (anyFileUpdated) {
					try (FileOutputStream fos = new FileOutputStream(versionsFile)) {
						fos.write(localVersions.toString().getBytes());
					}
					callback.onUpdateFound();
					} else {
					callback.onNoUpdate();
				}
				
				} catch (Exception e) {
				Log.e(TAG, "خطأ أثناء التحديث", e);
				callback.onError(e.getMessage());
			}
		}).start();
	}
	
	private static boolean downloadFile(String fileUrl, File destFile) {
		try {
			// إضافة مانع الكاش لروابط تحميل الملفات أيضاً إذا كانت من GitHub Raw
			String downloadUrl = fileUrl;
			if(fileUrl.contains("raw.githubusercontent")) {
				downloadUrl += "?t=" + System.currentTimeMillis();
			}
			
			URL url = new URL(downloadUrl);
			HttpURLConnection conn = (HttpURLConnection) url.openConnection();
			if (conn.getResponseCode() != 200) return false;
			
			InputStream is = conn.getInputStream();
			FileOutputStream fos = new FileOutputStream(destFile);
			byte[] buffer = new byte[4096];
			int len;
			while ((len = is.read(buffer)) != -1) {
				fos.write(buffer, 0, len);
			}
			fos.close();
			is.close();
			return true;
			} catch (Exception e) {
			Log.e(TAG, "فشل تحميل الملف: " + fileUrl, e);
			return false;
		}
	}
}