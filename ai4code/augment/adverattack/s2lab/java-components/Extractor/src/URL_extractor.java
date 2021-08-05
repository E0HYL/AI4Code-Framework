import soot.*;
import soot.tagkit.Tag;

import java.util.List;


public class URL_extractor {



    private Soot_utlilty utility = new Soot_utlilty();

    public SootClass extract_class_url(String feature) {

        for (SootClass c : Scene.v().getApplicationClasses()) {
            if (utility.isExcludeClass(c)) {
                continue;
            }
            for(SootField f : c.getFields()){
                for(Tag t  :f.getTags()){
                    if(t.toString().contains(feature)){
                        return c;
                    }
                }

            }

            for (SootMethod m : c.getMethods()) {
                if (!m.hasActiveBody()) {
                    continue;
                }

                List<ValueBox> useBoxes = m.getActiveBody().getUseAndDefBoxes();
                for (ValueBox valueBox : useBoxes) {
                    String content = valueBox.getValue().toString();
                    if (content.contains(feature)) {
                        return c;
                    }
                }
            }
        }
        return null;
    }
}

